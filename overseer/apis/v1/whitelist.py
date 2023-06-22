from overseer.apis.v1.base import *

class Whitelist(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("endorsements", required=False, default=0, type=int, help="Limit to this amount of endorsements of more", location="args")
    get_parser.add_argument("guarantors", required=False, default=1, type=int, help="Limit to this amount of guarantors of more", location="args")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Whitelist_get, code=200, description='Instances', skip_none=True)
    def get(self):
        '''A List with the details of all instances and their endorsements
        '''
        self.args = self.get_parser.parse_args()
        instance_details = []
        for instance in database.get_all_instances(self.args.endorsements,self.args.guarantors):
            instance_details.append(instance.get_details())
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200



class WhitelistDomain(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")

    @api.expect(get_parser)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_instances, code=200, description='Instances')
    def get(self, domain):
        '''Display info about a specific instance
        '''
        self.args = self.get_parser.parse_args()
        instance = database.find_instance_by_domain(domain)
        if not instance:
            raise e.NotFound(f"No Instance found matching provided domain. Have you remembered to register it?")
        return instance.get_details(),200


    put_parser = reqparse.RequestParser()
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("guarantor", required=False, type=str, help="(Optiona) The domain of the guaranteeing instance. They will receive a PM to validate you", location="json")


    @api.expect(put_parser)
    @api.marshal_with(models.response_model_instances, code=200, description='Instances')
    @api.response(400, 'Bad Request', models.response_model_error)
    def put(self, domain):
        '''Register a new instance to the overseer
        An instance account has to exist in the overseer lemmylemmy instance
        That account will recieve the new API key via PM
        '''
        self.args = self.put_parser.parse_args()
        existing_instance = Instance.query.filter_by(domain=domain).first()
        if existing_instance:
            return existing_instance.get_details(),200
        if domain.endswith("test.dbzer0.com"):
            requested_lemmy = Lemmy(f"https://{domain}")
            requested_lemmy._requestor.nodeinfo = {"software":{"name":"lemmy"}}
            site = {"site_view":{"local_site":{"require_email_verification": True,"registration_mode":"open"}}}
        else:
            requested_lemmy = Lemmy(f"https://{domain}")
            site = requested_lemmy.site.get()
        if not site:
            raise e.BadRequest(f"Error encountered while polling domain {domain}. Please check it's running correctly")
        api_key = pm_new_api_key(domain)
        if not api_key:
            raise e.BadRequest("Failed to generate API Key")
        new_instance = Instance(
            domain=domain,
            api_key=hash_api_key(api_key),
            open_registrations=site["site_view"]["local_site"]["registration_mode"] == "open",
            email_verify=site["site_view"]["local_site"]["require_email_verification"],
            software=requested_lemmy.nodeinfo['software']['name'],
        )
        new_instance.create()
        return new_instance.get_details(),200

    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("regenerate_key", required=False, type=bool, help="If True, will PM a new api key to this instance", location="json")


    @api.expect(patch_parser)
    @api.marshal_with(models.response_model_instances, code=200, description='Instances', skip_none=True)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Instance Not Registered', models.response_model_error)
    def patch(self, domain):
        '''Regenerate API key for instance
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your overctrl.dbzer0.com account")
        instance = database.find_instance_by_api_key(self.args.apikey)
        if not instance:
            raise e.Forbidden(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if self.args.regenerate_key:
            new_key = pm_new_api_key(domain)
            instance.api_key = hash_api_key(new_key)
            db.session.commit()
        return instance.get_details(),200

    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")


    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Instances', skip_none=True)
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Forbidden', models.response_model_error)
    def delete(self, domain):
        '''Delete instance from overseer
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your overctrl.dbzer0.com account")
        instance = database.find_authenticated_instance(domain, self.args.apikey)
        if not instance:
            raise e.BadRequest(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if domain == os.getenv('OVERSEER_LEMMY_DOMAIN'):
            raise e.Forbidden("Cannot delete overseer control instance")
        db.session.delete(instance)
        db.session.commit()
        logger.warning(f"{domain} deleted")
        return {"message":'Changed'}, 200

