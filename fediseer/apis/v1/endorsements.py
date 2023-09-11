from fediseer.apis.v1.base import *
from fediseer.classes.instance import Endorsement,Censure
from fediseer.classes.reports import Report
from fediseer import enums

class Approvals(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domains_csv):
        '''Display all endorsements given out by one or more domains
        You can pass a comma-separated list of domain names and the results will be a set of all their
        endorsements together.
        '''
        domains_list = domains_csv.split(',')
        self.args = self.get_parser.parse_args()
        instances = database.find_multiple_instance_by_domains(domains_list)
        if not instances:
            raise e.NotFound(f"No Instances found matching any of the provided domains. Have you remembered to register them?")
        instance_details = []
        for instance in database.get_all_endorsed_instances_by_approving_id([instance.id for instance in instances]):
            instance_details.append(instance.get_details())
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

class Endorsements(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all endorsements received by a specific domain
        '''
        self.args = self.get_parser.parse_args()
        instance = database.find_instance_by_domain(domain)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided domain. Have you remembered to register it?")
        instance_details = []
        for instance in database.get_all_approving_instances_by_endorsed_id(instance.id):
            instance_details.append(instance.get_details())
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")


    @api.expect(put_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Endorse Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Endorse an instance
        An endorsement signifies an approval from your instance to how that instance is being run.
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can endorse others.")
        if instance.domain == domain:
            raise e.BadRequest("Nice try, but you can't endorse yourself.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance, nodeinfo, admin_usernames = ensure_instance_registered(domain)
        if not target_instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        if len(target_instance.guarantors) == 0:
            raise e.Forbidden("Not Guaranteed instances can be endorsed. Please guarantee for them, or find someone who will.")
        if not target_instance:
            raise e.BadRequest("Instance to endorse not found")
        if database.get_censure(target_instance.id,instance.id):
            raise e.BadRequest("You can't endorse an instance you've censured! Please withdraw the censure first.")
        if database.get_endorsement(target_instance.id,instance.id):
            return {"message":'OK'}, 200
        new_endorsement = Endorsement(
            approving_id=instance.id,
            endorsed_id=target_instance.id,
        )
        db.session.add(new_endorsement)
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_instance.domain,
            report_type=enums.ReportType.ENDORSEMENT,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        if not database.has_recent_endorsement(target_instance.id):
            activitypub_pm.pm_admins(
                message=f"Your instance has just been [endorsed](https://fediseer.com/faq#what-is-an-endorsement) by {instance.domain}",
                domain=target_instance.domain,
                software=target_instance.software,
                instance=target_instance,
            )
        logger.info(f"{instance.domain} Endorsed {domain}")
        return {"message":'Changed'}, 200


    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Withdraw Instance Endorsement')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def delete(self,domain):
        '''Withdraw an instance endorsement
        '''
        self.args = self.delete_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to withdraw endorsement not found")
        endorsement = database.get_endorsement(target_instance.id,instance.id)
        if not endorsement:
            return {"message":'OK'}, 200
        db.session.delete(endorsement)
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_instance.domain,
            report_type=enums.ReportType.ENDORSEMENT,
            report_activity=enums.ReportActivity.DELETED,
        )
        db.session.add(new_report)
        db.session.commit()
        activitypub_pm.pm_admins(
            message=f"Oh no. {instance.domain} has just withdrawn the endorsement of your instance",
            domain=target_instance.domain,
            software=target_instance.software,
            instance=target_instance,
        )
        logger.info(f"{instance.domain} Withdrew endorsement from {domain}")
        return {"message":'Changed'}, 200
