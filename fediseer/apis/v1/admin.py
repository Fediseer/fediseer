from fediseer.apis.v1.base import *
from fediseer import enums
from fediseer.classes.reports import Report
from fediseer.register import ensure_instance_registered
from fediseer.classes.instance import InstanceFlag

class Flag(Resource):

    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("comment", required=False, type=str, help="provide a reasoning for this flag", location="json")
    put_parser.add_argument("flag", required=True, type=str, help="The flag to apply", location="json")


    @api.expect(put_parser,models.input_flag_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Action Result')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)

    def put(self, domain):
        '''Flag an instance
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to the admin account")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.Forbidden("Only a fediseer admin can modify instance flags")
        if user.account != "@fediseer@fediseer.com":
            raise e.Forbidden("Only a fediseer admin can modify instance flags")
        admin_instance = database.find_instance_by_user(user)
        target_instance, instance_info = ensure_instance_registered(domain)
        flag = enums.InstanceFlags[self.args.flag]
        if database.instance_has_flag(target_instance.id,flag):
            return {"message": "OK"},200
        new_flag = InstanceFlag(
            instance_id = target_instance.id,
            flag = flag,
            comment = self.args.comment,
        )
        db.session.add(new_flag)
        if flag == enums.InstanceFlags.RESTRICTED and not database.instance_has_flag(target_instance.id,enums.InstanceFlags.MUTED):
            muted_flag = InstanceFlag(
                instance_id = target_instance.id,
                flag = enums.InstanceFlags.MUTED,
                comment = "Restricted with reason: " + self.args.comment,
            )
            db.session.add(muted_flag)
        # Sactioned instances get no visibility
        if flag in [enums.InstanceFlags.MUTED,enums.InstanceFlags.RESTRICTED]:
            target_instance.visibility_censures = enums.ListVisibility.PRIVATE
            target_instance.visibility_endorsements = enums.ListVisibility.PRIVATE
            target_instance.visibility_hesitations = enums.ListVisibility.PRIVATE
        new_report = Report(
            source_domain=admin_instance.domain,
            target_domain=target_instance.domain,
            report_type=enums.ReportType.FLAG,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        return {"message": "Changed"},200
        
    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("comment", required=False, type=str, help="provide a reasoning for this flag", location="json")
    patch_parser.add_argument("flag", required=False, type=str, help="The flag to apply", location="json")


    @api.expect(patch_parser,models.input_flag_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Action Result')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance or flag not found', models.response_model_error)
    def patch(self, domain):
        '''Modify an instance's flag
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to the admin account")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.Forbidden("Only a fediseer admin can modify instance flags")
        if user.account != "@fediseer@fediseer.com":
            raise e.Forbidden("Only a fediseer admin can modify instance flags")
        admin_instance = database.find_instance_by_user(user)
        target_instance, instance_info = ensure_instance_registered(domain)
        flag = enums.InstanceFlags[self.args.flag]
        existing_flag = database.get_instance_flag(target_instance.id,flag)
        if not existing_flag:
            raise e.NotFound(f"{flag.name} not found in {domain}")
        if existing_flag.comment == self.args.comment:
            return {"message": "OK"},200
        existing_flag.comment = self.args.comment,
        new_report = Report(
            source_domain=admin_instance.domain,
            target_domain=target_instance.domain,
            report_type=enums.ReportType.FLAG,
            report_activity=enums.ReportActivity.MODIFIED,
        )
        db.session.add(new_report)
        db.session.commit()
        return {"message": "Changed"},200
        

    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    delete_parser.add_argument("flag", required=False, type=str, help="The flag to delete", location="json")


    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Instances', skip_none=True)
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Forbidden', models.response_model_error)
    def delete(self, domain):
        '''Delete an instance's flag
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to the admin account")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.Forbidden("Only a fediseer admin can delete instance flags")
        if user.account != "@fediseer@fediseer.com":
            raise e.Forbidden("Only a fediseer admin can delete instance flags")
        admin_instance = database.find_instance_by_user(user)
        target_instance, instance_info = ensure_instance_registered(domain)
        flag = enums.InstanceFlags[self.args.flag]
        existing_flag = database.get_instance_flag(target_instance.id,flag)
        if not existing_flag:
            return {"message": "OK"},200
        db.session.delete(existing_flag)
        new_report = Report(
            source_domain=admin_instance.domain,
            target_domain=target_instance.domain,
            report_type=enums.ReportType.FLAG,
            report_activity=enums.ReportActivity.DELETED,
        )
        db.session.add(new_report)
        db.session.commit()
        return {"message": "Changed"},200