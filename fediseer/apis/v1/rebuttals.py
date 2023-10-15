from fediseer.apis.v1.base import *
from fediseer.classes.instance import Rebuttal
from fediseer.utils import sanitize_string
from fediseer.classes.reports import Report
from fediseer import enums

class Rebuttals(Resource):
    decorators = [limiter.limit("45/minute"), limiter.limit("30/minute", key_func = get_request_path)]
    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("rebuttal", default=None, type=str, required=True, location="json")


    @api.expect(put_parser,models.input_rebuttals_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Rebut Censure or Hesitation against your instance')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def put(self, domain):
        '''Rebut a Censure or Hesitation against your instance
        Use this to provide evidence against, or to initiate discussion
        '''
        self.args = self.put_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if len(instance.guarantors) == 0:
            raise e.Forbidden("Only guaranteed instances can rebut.")
        if database.instance_has_flag(instance.id,enums.InstanceFlags.RESTRICTED):
            raise e.Forbidden("You cannot take this action as your instance is restricted")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        unbroken_chain, chainbreaker = database.has_unbroken_chain(instance.id)
        if not unbroken_chain:
            raise e.Forbidden(f"Guarantee chain for this instance has been broken. Chain ends at {chainbreaker.domain}!")
        target_instance = database.find_instance_by_domain(domain)
        if not target_instance:
            raise e.NotFound(f"Instance {domain} is not registered on the fediseer.")
        if database.get_rebuttal(target_instance.id,instance.id):
            return {"message":'OK'}, 200
        censure = database.get_censure(instance.id, target_instance.id)
        if not censure or target_instance.visibility_censures != enums.ListVisibility.OPEN:
            hesitation = database.get_hesitation(instance.id, target_instance.id)
            if not hesitation or target_instance.visibility_hesitations != enums.ListVisibility.OPEN:
                raise e.BadRequest(f"Either no censure or hesitation from {domain} found towards {instance.domain}, or they are not openly visible.")
        rebuttal_value = self.args.rebuttal
        if rebuttal_value is not None:
            rebuttal_value = sanitize_string(rebuttal_value)
        new_rebuttal = Rebuttal(
            source_id=instance.id,
            target_id=target_instance.id,
            rebuttal=rebuttal_value,
        )
        db.session.add(new_rebuttal)
        target_domain = target_instance.domain
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.REBUTTAL,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} Rebutted {domain}")
        return {"message":'Changed'}, 200


    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("rebuttal", default=None, type=str, required=False, location="json")


    @api.expect(patch_parser,models.input_rebuttals_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Modify Rebuttal')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Not Guaranteed', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def patch(self, domain):
        '''Modify a Rebuttal
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        target_instance = database.find_instance_by_domain(domain=domain)
        if not target_instance:
            raise e.BadRequest("Instance from which to modify censure not found")
        rebuttal = database.get_rebuttal(target_instance.id,instance.id)
        if not rebuttal:
            raise e.BadRequest(f"No Rebuttal found for {domain} from {instance.domain}")
        changed = False
        rebuttal_value = self.args.rebuttal
        if rebuttal_value is not None:
            rebuttal_value = sanitize_string(rebuttal_value)
            if rebuttal.rebuttal != rebuttal_value:
                rebuttal.rebuttal = rebuttal_value
                changed = True
        if changed is False:
            return {"message":'OK'}, 200
        target_domain = target_instance.domain
        if instance.visibility_censures != enums.ListVisibility.OPEN:
            target_domain = '[REDACTED]'
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.REBUTTAL,
            report_activity=enums.ReportActivity.MODIFIED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} modified rebuttal about {domain}")
        return {"message":'Changed'}, 200


    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Delete Rebuttal')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(404, 'Instance not registered', models.response_model_error)
    def delete(self,domain):
        '''Delete a rebuttal
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
        rebuttal = database.get_rebuttal(target_instance.id,instance.id)
        if not rebuttal:
            return {"message":'OK'}, 200
        db.session.delete(rebuttal)
        target_domain = target_instance.domain
        new_report = Report(
            source_domain=instance.domain,
            target_domain=target_domain,
            report_type=enums.ReportType.REBUTTAL,
            report_activity=enums.ReportActivity.DELETED,
        )
        db.session.add(new_report)
        db.session.commit()
        logger.info(f"{instance.domain} delete rebuttal about {domain}")
        return {"message":'Changed'}, 200
