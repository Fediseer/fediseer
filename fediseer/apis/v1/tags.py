from fediseer.apis.v1.base import *
from fediseer import enums
from fediseer.classes.reports import Report
from fediseer.classes.instance import InstanceTag

class Tag(Resource):

    put_parser = reqparse.RequestParser()
    put_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("tags", required=True, type=list, help="The tags to apply", location="json")


    @api.expect(put_parser,models.input_flag_modify, validate=True)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Action Result')
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)

    def put(self):
        '''Tag your instance.
        No hate speech allowed!
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to the admin account of this instance")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.Forbidden("Instance not found. Have you remembed to claim it?")
        instance = database.find_instance_by_user(user)
        if len(self.args.tags) == 0:
            raise e.BadRequest("You must provide at least one tag to add")
        changed = False
        for tag in self.args.tags:
            if database.instance_has_tag(instance.id,tag):
                continue
            new_tag = InstanceTag(
                instance_id = instance.id,
                tag = tag,
            )
            db.session.add(new_tag)
            changed = True
        if changed:
            db.session.commit()
            return {"message": "Changed"},200
        return {"message": "OK"},200
        
    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    delete_parser.add_argument("tags", required=True, type=list, help="The tags to delete", location="json")


    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Instances', skip_none=True)
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Forbidden', models.response_model_error)
    def delete(self):
        '''Delete an instance's flag
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to the admin account")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.Forbidden("Instance not found. Have you remembed to claim it?")
        instance = database.find_instance_by_user(user)
        if len(self.args.tags) == 0:
            raise e.BadRequest("You must provide at least one tag to add")
        changed = False
        for tag in self.args.tags:
            existing_tag = database.get_instance_tag(instance.id,tag)
            if not existing_tag:
                existing_tag
            db.session.delete(existing_tag)
        if changed:
            db.session.commit()
            return {"message": "Changed"},200
        return {"message": "OK"},200