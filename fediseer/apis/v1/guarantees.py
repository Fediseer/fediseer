from fediseer.apis.v1.base import *
from fediseer.classes.instance import Guarantee, Endorsement, RejectionRecord

class Guarantors(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all guarantees given by a specific domain
        '''
        self.args = self.get_parser.parse_args()
        instance = database.find_instance_by_domain(domain)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided domain. Have you remembered to register it?")
        instance_details = []
        for guaranteed in database.get_all_guaranteed_instances_by_guarantor_id(instance.id):
            instance_details.append(guaranteed.get_details())
        if self.args.csv:
            return {"csv": ",".join([guaranteed["domain"] for guaranteed in instance_details])},200
        if self.args.domains:
            return {"domains": [guaranteed["domain"] for guaranteed in instance_details]},200
        return {"instances": instance_details},200
    
class Guarantees(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all instances guaranteeing for this domain
        '''
        self.args = self.get_parser.parse_args()
        instance = database.find_instance_by_domain(domain)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided domain. Have you remembered to register it?")
        instance_details = []
        for guarantor in database.get_all_guarantor_instances_by_guaranteed_id(instance.id):
            instance_details.append(guarantor.get_details())
        if self.args.csv:
            return {"csv": ",".join([guarantor["domain"] for guarantor in instance_details])},200
        if self.args.domains:
            return {"domains": [guarantor["domain"] for guarantor in instance_details]},200
        logger.debug(database.get_guarantor_chain(instance.id))
        return {"instances": instance_details},200

    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")


    @api.expect(put_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Endorse Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Instance Not Guaranteed or Tartget instance Guaranteed by others', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Guarantee an instance
        A instance can only be guaranteed by one other instance
        An instance can guarantee up to 20 other instances
        A guaranteed instance can guarantee and endorse other instances.
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your overctrl.dbzer0.com account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can guarantee others.")
        if len(instance.guarantees) >= 20 and instance.id != 0:
            raise e.Forbidden("You cannot guarantee for more than 20 instances")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance, nodeinfo, admin_usernames = ensure_instance_registered(domain)
        if not target_instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        if database.get_guarantee(target_instance.id,instance.id):
            return {"message":'OK'}, 200
        gdomain = target_instance.get_guarantor_domain()
        if gdomain:
            raise e.Forbidden(f"Target instance already guaranteed by {gdomain}")
        new_guarantee = Guarantee(
            guaranteed_id=target_instance.id,
            guarantor_id=instance.id,
        )
        db.session.add(new_guarantee)
        # Guaranteed instances get their automatic first endorsement
        new_endorsement = Endorsement(
            approving_id=instance.id,
            endorsed_id=target_instance.id,
        )
        db.session.add(new_endorsement)
        db.session.commit()
        activitypub_pm.pm_admins(
            message=f"Congratulations! Your instance has just been guaranteed by {instance.domain}. This also comes with your first endorsement.\n\nThis is an automated PM by the [Fediseer](https://fediseer.com) service.",
            domain=target_instance.domain,
            software=target_instance.software,
            instance=target_instance,
        )
        orphan_ids = database.get_guarantee_chain(target_instance.id)
        for orphan in database.get_instances_by_ids(orphan_ids):
            activitypub_pm.pm_admins(
                message=f"Phew! You guarantor chain has been repaired as {instance.domain} has guaranteed for {domain}.",
                domain=orphan.domain,
                software=orphan.software,
                instance=orphan,
            )
            orphan.unset_as_orphan()
        logger.info(f"{instance.domain} Guaranteed for {domain}")
        return {"message":'Changed'}, 200


    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Withdraw Instance Guarantee')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def delete(self,domain):
        '''Withdraw an instance guarantee
        '''
        self.args = self.delete_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your overctrl.dbzer0.com account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to withdraw endorsement not found")
        # If API key matches the target domain, we assume they want to remove the guarantee added to them to allow another domain to guarantee them
        if instance.id == target_instance.id:
            guarantee = instance.get_guarantee()
        else:
            guarantee = database.get_guarantee(target_instance.id,instance.id)
        if not guarantee:
            return {"message":'OK'}, 200
        if database.has_recent_rejection(target_instance.id,instance.id):
            raise e.Forbidden("You cannot remove your guarantee from the same instance within 24 hours")
        # Removing a guarantee removes the endorsement
        endorsement = database.get_endorsement(target_instance.id,instance.id)
        if endorsement:
            db.session.delete(endorsement)
        db.session.delete(guarantee)
        rejection_record = database.get_rejection_record(instance.id,target_instance.id)
        if rejection_record:
            rejection_record.refresh()
        else:
            rejection = RejectionRecord(
                rejected_id=target_instance.id,
                rejector_id=instance.id,
            )
            db.session.add(rejection)
        db.session.commit()
        activitypub_pm.pm_admins(
            message=f"Attention! You guarantor instance {instance.domain} has withdrawn their backing.\n\n"
                    "IMPORTANT: The instances you vouched for are still considered guaraneed but cannot guarantee or endorse others"
                    "If you find a new guarantor then your guarantees will be reactivated!.\n\n"
                    "Note that if you do not find a guarantor within 7 days, all your guarantees and endorsements will be removed.",
            domain=target_instance.domain,
            software=target_instance.software,
            instance=target_instance,
        )
        orphan_ids = database.get_guarantee_chain(target_instance.id)
        for orphan in database.get_instances_by_ids(orphan_ids):
            activitypub_pm.pm_admins(
                message=f"Attention! You guarantor chain has been broken because {instance.domain} has withdrawn their backing from {domain}.\n\nIMPORTANT: All your guarantees will be deleted unless the chain is repaired or you find a new guarantor within 24hours!",
                domain=orphan.domain,
                software=orphan.software,
                instance=orphan,
            )
            orphan.set_as_oprhan()
        logger.info(f"{instance.domain} Withdrew guarantee from {domain}")
        return {"message":'Changed'}, 200