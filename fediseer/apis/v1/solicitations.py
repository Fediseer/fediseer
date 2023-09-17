from fediseer.apis.v1.base import *
from fediseer.messaging import activitypub_pm
from fediseer import enums
from fediseer.classes.instance import Solicitation
from fediseer.classes.reports import Report

class Solicitations(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser, query_string=True)
    @cache.cached(timeout=10)
    @api.marshal_with(models.response_model_model_Solicitation_get, code=200, description='Soliciting Instances', skip_none=True)
    def get(self):
        '''A List with all the currently open solicitations for guarantees.
        '''
        self.args = self.get_parser.parse_args()
        instance_details = []
        for instance in database.get_all_solicitations():
            instance_detail = instance.get_details()
            instance_detail["comment"] = database.find_latest_solicitation_by_source(instance.id).comment
            instance_details.append(instance_detail)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200

    decorators = [limiter.limit("20/minute", key_func = get_request_path)]
    post_parser = reqparse.RequestParser()
    post_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    post_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    post_parser.add_argument("guarantor", required=False, type=str, help="(Optional) The domain of a guaranteeing instance. They will receive a PM to validate you", location="json")
    post_parser.add_argument("comment", required=False, type=str, location="json")

    @api.expect(post_parser,models.input_solicit, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Instances')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Recent solicitation exists', models.response_model_error)
    @api.response(404, 'Instance not claimed', models.response_model_error)
    def post(self):
        '''Solicit a guarantee
        This will add your instance to the list of requested guarantees, 
        Other guaranteeed instances can review your application and decide to guarantee for you.
        You can optionally provide the domain of an instance to receive a PM requesting for your guarantee
        '''
        self.args = self.post_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your admin account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided API key and domain. Have you remembered to claim it?")
        if instance.is_guaranteed():
            raise e.BadRequest(f"Your instance is already guaranteed by {instance.get_guarantor().domain}")
        if database.has_too_many_actions_per_min(instance.domain):
            raise e.TooManyRequests("Your instance is doing more than 20 actions per minute. Please slow down.")
        guarantor_instance = None
        if self.args.guarantor:
            guarantor_instance = database.find_instance_by_domain(self.args.guarantor)
            if not guarantor_instance:
                raise e.BadRequest(f"Requested guarantor domain {self.args.guarantor} is not registered with the Fediseer yet!")
            existing_solicitation = database.find_solicitation_by_target(instance.id,guarantor_instance.id)
            if existing_solicitation:
                raise e.Forbidden(f"You have already solicited this instance for a guarantee. Please solicit a different guarantor instead.")
        else:
            existing_solicitation = database.find_solicitation_by_target(instance.id,None)
            if existing_solicitation:
                raise e.Forbidden(f"You have already solicited an open-ended guarantee. Please try to solicit from a specific instance next.")
        if database.has_recent_solicitations(instance.id):
            raise e.Forbidden(f"You can only solicit one guarantee per day.")
        new_solicitation = Solicitation(
            comment=self.args.comment,
            source_id=instance.id,
            target_id=guarantor_instance.id if guarantor_instance else None,
        )
        db.session.add(new_solicitation)
        new_report = Report(
            source_domain=instance.domain,
            target_domain=guarantor_instance.domain if guarantor_instance else instance.domain,
            report_type=enums.ReportType.SOLICITATION,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        if guarantor_instance:
            try:
                activitypub_pm.pm_admins(
                    message=f"New instance {instance.domain} was just registered with the Fediseer and have solicited [your guarantee](https://gui.fediseer.com/guarantees/guarantee)!",
                    domain=guarantor_instance.domain,
                    software=guarantor_instance.software,
                    instance=guarantor_instance,
                )
            except:
                pass
        return {"message":'Changed'}, 200