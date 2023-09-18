from fediseer.apis.v1.base import *


class FindInstance(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")


    @api.expect(get_parser)
    @api.marshal_with(models.response_model_instances_visibility, code=200, description='Instance', skip_none=True)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    def get(self):
        '''Retrieve instance information via API Key
        '''
        self.args = self.get_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd admin account")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.NotFound("API key not found. Please Claim an instance first and use the API key that is PM'd to you")
        instance = database.find_instance_by_user(user)
        return instance.get_details(show_visibilities=True),200
