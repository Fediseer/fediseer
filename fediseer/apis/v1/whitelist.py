from fediseer.apis.v1.base import *
from fediseer.messaging import activitypub_pm
from fediseer.fediverse import get_admin_for_software, get_nodeinfo
from fediseer.classes.user import User, Claim
from fediseer.consts import SUPPORTED_SOFTWARE

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
        instance, nodeinfo, site, admin_usernames = self.ensure_instance_registered(domain)
        if not instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        return instance.get_details(),200


    put_parser = reqparse.RequestParser()
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("admin", required=False, type=str, help="The username of the admin who wants to register this domain", location="json")
    put_parser.add_argument("guarantor", required=False, type=str, help="(Optiona) The domain of the guaranteeing instance. They will receive a PM to validate you", location="json")


    @api.expect(put_parser)
    @api.marshal_with(models.response_model_instances, code=200, description='Instances')
    @api.response(400, 'Bad Request', models.response_model_error)
    def put(self, domain):
        '''Claim an fediverse instance.
        If the instance hasn't been recorded yet it will be polled and added.
        You must specify an admin account which will recieve the new API key via Private Message.
        '''
        self.args = self.put_parser.parse_args()
        if '@' in self.args.admin:
            raise e.BadRequest("Please send the username without any @ signs or domains")
        instance, nodeinfo, site, admin_usernames = self.ensure_instance_registered(domain)
        guarantor_instance = None
        if self.args.guarantor:
            guarantor_instance = database.find_instance_by_domain(self.args.guarantor)
            if not guarantor_instance:
                raise e.BadRequest(f"Requested guarantor domain {self.args.guarantor} is not registered with the Overseer yet!")
        if self.args.admin not in admin_usernames:
            raise e.Forbidden(f"Only admins of that {instance.software} are allowed to claim it.")
        existing_claim = database.find_claim(f"@{self.args.admin}@{domain}")
        if existing_claim:
            raise e.Forbidden(f"You have already claimed this instance as this admin. Please use the PATCH method to reset your API key.")
        api_key = activitypub_pm.pm_new_api_key(domain, self.args.admin, instance.software)
        if not api_key:
            raise e.BadRequest("Failed to generate API Key")
        new_user = User(
            api_key=hash_api_key(api_key),
            account=f"@{self.args.admin}@{domain}",
            username=self.args.admin,
        )
        db.session.add(new_user)
        db.session.commit()
        new_claim = Claim(
            user_id = new_user.id,
            instance_id = instance.id,
        )
        db.session.add(new_claim)
        db.session.commit()
        if guarantor_instance:
            activitypub_pm.pm_admins(
                message=f"New instance {domain} was just registered with the Overseer and have asked you to guarantee for them!",
                domain=guarantor_instance.domain,
                software=guarantor_instance.software,
                instance=guarantor_instance,
            )
        return instance.get_details(),200

    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("regenerate_key", required=False, type=str, help="If a username is given, their API will be reset. This can be initiated by other instance admins or the fediseer.", location="json")


    @api.expect(patch_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Instances', skip_none=True)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Instance Not Registered', models.response_model_error)
    def patch(self, domain):
        '''Regenerate API key for instance
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd admin account")
        user = database.find_user_by_api_key(self.args.apikey)
        if not user:
            raise e.Forbidden("You have not yet claimed an instance. Use the POST method to do so.")
        instance = database.find_instance_by_user(user)
        if self.args.regenerate_key:
            requestor = None
            if self.args.regenerate_key != user.username or user.username == "fediseer":
                requestor = user.username
                instance_to_reset = database.find_instance_by_account(f"@{self.args.regenerate_key}@{domain}")
                if instance != instance_to_reset and user.username != "fediseer":
                    raise e.BadRequest("Only other admins or the fediseer can request API key reset for others.")
                instance = instance_to_reset
                user = database.find_user_by_account(f"@{self.args.regenerate_key}@{domain}")
            new_key = activitypub_pm.pm_new_api_key(domain, self.args.regenerate_key, instance.software, requestor=requestor)
            user.api_key = hash_api_key(new_key)
            db.session.commit()
            return {"message": "Changed"},200

    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    delete_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    delete_parser.add_argument("username", required=False, type=str, help="(Not Implemented) Provide the username of another admin to remove their API key", location="json")


    @api.expect(delete_parser)
    @api.marshal_with(models.response_model_simple_response, code=200, description='Instances', skip_none=True)
    @api.response(400, 'Bad Request', models.response_model_error)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Forbidden', models.response_model_error)
    def delete(self, domain):
        '''Delete claim to instance (Not implemented)
        '''
        return e.BadRequest("Not implemented")
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your account")
        instance = database.find_authenticated_instance(domain, self.args.apikey)
        if not instance:
            raise e.BadRequest(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if domain == os.getenv('FEDISEER_LEMMY_DOMAIN'):
            raise e.Forbidden("Cannot delete fediseer control instance")
        db.session.delete(instance)
        db.session.commit()
        logger.warning(f"{domain} deleted")
        return {"message":'Changed'}, 200

    def ensure_instance_registered(self, domain):        
        if domain.endswith("test.dbzer0.com"):
            # Fake instances for testing chain of trust
            requested_lemmy = Lemmy(f"https://{domain}")
            requested_lemmy._requestor.nodeinfo = {"software":{"name":"lemmy"}}
            open_registrations = False
            email_verify = True
            software = "lemmy"
            admin_usernames = ["db0"]
            nodeinfo = get_nodeinfo("lemmy.dbzer0.com")
            requested_lemmy = Lemmy(f"https://{domain}")
            site = requested_lemmy.site.get()
        else:
            nodeinfo = get_nodeinfo(domain)
            if not nodeinfo:
                raise e.BadRequest(f"Error encountered while polling domain {domain}. Please check it's running correctly")
            software = nodeinfo["software"]["name"]
            if software not in SUPPORTED_SOFTWARE:
                raise e.BadRequest(f"Fediverse software {software} not supported at this time")
            if software == "lemmy":
                requested_lemmy = Lemmy(f"https://{domain}")
                site = requested_lemmy.site.get()
                if not site:
                    raise e.BadRequest(f"Error encountered while polling lemmy domain {domain}. Please check it's running correctly")
                open_registrations = site["site_view"]["local_site"]["registration_mode"] == "open"
                email_verify = site["site_view"]["local_site"]["require_email_verification"]
                software = software
                admin_usernames = [a["person"]["name"] for a in site["admins"]]
            else:
                open_registrations = nodeinfo["openRegistrations"]
                email_verify = False
                admin_usernames = get_admin_for_software(software, domain)
        instance = database.find_instance_by_domain(domain)
        if instance:
            return instance, nodeinfo, site, admin_usernames
        new_instance = Instance(
            domain=domain,
            open_registrations=open_registrations,
            email_verify=email_verify,
            software=software,
        )
        new_instance.create()
        return new_instance, nodeinfo, site, admin_usernames
