from fediseer.apis.v1.base import *
from fediseer.classes.instance import Censure,Endorsement
from fediseer.utils import sanitize_string

class CensuresGiven(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domains_csv):
        '''Display all censures given out by one or more domains
        You can pass a comma-separated list of domain names
        and the results will be a set of all their censures together.
        '''
        domains_list = domains_csv.split(',')
        self.args = self.get_parser.parse_args()
        instances = database.find_multiple_instance_by_domains(domains_list)
        if not instances:
            raise e.NotFound(f"No Instances found matching any of the provided domains. Have you remembered to register them?")
        instance_details = []
        for c_instance in database.get_all_censured_instances_by_censuring_id([instance.id for instance in instances]):
            censures = database.get_all_censure_reasons_for_censured_id(c_instance.id, [instance.id for instance in instances])
            c_instance_details = c_instance.get_details()
            if len(censures) > 0:
                c_instance_details["censure_reasons"] = [censure.reason for censure in censures]
            instance_details.append(c_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        
        return {"instances": instance_details},200

class Censures(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def get(self, domain):
        '''Display all censures received by a specific domain
        '''
        self.args = self.get_parser.parse_args()
        instance = database.find_instance_by_domain(domain)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided domain. Have you remembered to register it?")
        instance_details = []
        for c_instance in database.get_all_censuring_instances_by_censured_id(instance.id):
            censures = database.get_all_censure_reasons_for_censured_id(instance.id, [c_instance.id])
            c_instance_details = c_instance.get_details()
            if len(censures) > 0:
                c_instance_details["censure_reasons"] = [censure.reason for censure in censures]
            instance_details.append(c_instance_details)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("reason", default=None, type=str, required=False, location="json")


    @api.expect(put_parser,models.input_censures_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Endorse Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Censure an instance
        A censure signifies a strong disapproval from your instance to how that instance is being run.
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can censure others.")
        if instance.domain == domain:
            raise e.BadRequest("You're a mad lad, but you can't censure yourself.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance, nodeinfo, admin_usernames = ensure_instance_registered(domain)
        if not target_instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        if not target_instance:
            raise e.BadRequest("Instance to censure not found")
        if database.get_endorsement(target_instance.id,instance.id):
            raise e.BadRequest("You can't censure an instance you've endorsed! Please withdraw the endorsement first.")
        if database.get_censure(target_instance.id,instance.id):
            return {"message":'OK'}, 200
    
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
        new_censure = Censure(
            censuring_id=instance.id,
            censured_id=target_instance.id,
            reason=reason,
        )
        db.session.add(new_censure)
        db.session.commit()
        logger.info(f"{instance.domain} Censured {domain}")
        return {"message":'Changed'}, 200


    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("reason", default=None, type=str, required=False, location="json")


    @api.expect(patch_parser,models.input_censures_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Endorse Instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def patch(self, domain):
        '''Modify an instance's Censure
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to modify censure not found")
        censure = database.get_censure(target_instance.id,instance.id)
        if not censure:
            raise e.BadRequest(f"No censure found for {domain} from {instance.domain}")
        reason = self.args.reason
        if reason is not None:
            reason = sanitize_string(reason)
        logger.debug([censure.reason,reason])
        if censure.reason == reason:
            return {"message":'OK'}, 200
        censure.reason = reason
        db.session.commit()
        logger.info(f"{instance.domain} Modfied censure for {domain}")
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
        '''Withdraw an instance censure
        '''
        self.args = self.delete_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to withdraw censure not found")
        censure = database.get_censure(target_instance.id,instance.id)
        if not censure:
            return {"message":'OK'}, 200
        db.session.delete(censure)
        db.session.commit()
        logger.info(f"{instance.domain} Withdrew censure from {domain}")
        return {"message":'Changed'}, 200