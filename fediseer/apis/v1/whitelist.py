from fediseer.apis.v1.base import *
from fediseer.messaging import activitypub_pm
from fediseer.classes.user import User, Claim
from fediseer import enums
from fediseer.classes.instance import Solicitation
from fediseer.classes.reports import Report
from fediseer.register import ensure_instance_registered

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
            instance_details.append(instance.get_details(show_visibilities=True))
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
    @api.marshal_with(models.response_model_instances_visibility, code=200, description='Instances')
    def get(self, domain):
        '''Display info about a specific instance
        '''
        self.args = self.get_parser.parse_args()
        try:
            instance, instance_info = ensure_instance_registered(domain)
        except Exception as err:
            # If the domain had been previously registered, we return its cached info
            instance = database.find_instance_by_domain(domain)
            if not instance:
                raise err
        if not instance:
            raise e.NotFound(f"Something went wrong trying to register this instance.")
        return instance.get_details(show_visibilities=True),200


    put_parser = reqparse.RequestParser()
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("admin", required=True, type=str, help="The username of the admin who wants to register this domain", location="json")
    put_parser.add_argument("guarantor", required=False, type=str, help="(Optional) The domain of another guaranteed instance. They will receive a PM to validate you and you will be added to the solicitations list.", location="json")
    put_parser.add_argument("pm_proxy", required=False, type=str, help="(Optional) If you do receive the PM from @fediseer@fediseer.com, set this to true to make the Fediseer PM your your API key via @fediseer@botsin.space. For this to work, ensure that botsin.space is not blocked in your instance and optimally follow @fediseer@botsin.space as well. If set, this will be used permanently for communication to your instance.", location="json")


    @api.expect(put_parser,models.input_instance_claim, validate=True)
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
        instance, instance_info = ensure_instance_registered(domain)
        guarantor_instance = None
        if self.args.guarantor:
            guarantor_instance = database.find_instance_by_domain(self.args.guarantor)
            if not guarantor_instance:
                raise e.BadRequest(f"Requested guarantor domain {self.args.guarantor} is not registered with the Fediseer yet!")
        if self.args.admin not in instance_info.admin_usernames:
            if len(instance_info.admin_usernames) == 0:
                raise e.Unauthorized(f"We could not discover any admins for this instance software. Please Ensure your software exposes this info. If it's exposed in a novel manner, consider sending us a PR to be able to retrieve this infomation.")
            else:
                raise e.Forbidden(f"Only admins of that {instance.software} are allowed to claim it.")
        existing_claim = database.find_claim(f"@{self.args.admin}@{domain}")
        if existing_claim:
            raise e.Forbidden(f"You have already claimed this instance as this admin. Please use the PATCH method to reset your API key.")
        if self.args.pm_proxy is not None:
            proxy = enums.PMProxy[self.args.pm_proxy]
            if instance.pm_proxy != proxy:
                instance.pm_proxy = proxy
        api_key = activitypub_pm.pm_new_api_key(
            domain=domain, 
            username=self.args.admin, 
            software=instance.software,
            proxy=instance.pm_proxy,
        )
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
        new_report = Report(
            source_domain=instance.domain,
            target_domain=instance.domain,
            report_type=enums.ReportType.CLAIM,
            report_activity=enums.ReportActivity.ADDED,
        )
        db.session.add(new_report)
        db.session.commit()
        if guarantor_instance and not instance.is_guaranteed():
            new_solicitation = Solicitation(
                source_id=instance.id,
                target_id=guarantor_instance.id,
            )
            db.session.add(new_solicitation)
            solicitation_report = Report(
                source_domain=instance.domain,
                target_domain=guarantor_instance.domain,
                report_type=enums.ReportType.SOLICITATION,
                report_activity=enums.ReportActivity.ADDED,
            )
            db.session.add(solicitation_report)
            db.session.commit()
            try:
                activitypub_pm.pm_admins(
                    message=f"New instance {instance.domain} was just registered with the Fediseer and have solicited [your guarantee](https://gui.fediseer.com/guarantees/guarantee)!",
                    domain=guarantor_instance.domain,
                    software=guarantor_instance.software,
                    instance=guarantor_instance,
                )
            except:
                pass
        return instance.get_details(),200

    patch_parser = reqparse.RequestParser()
    patch_parser.add_argument("apikey", type=str, required=True, help="The sending instance's API key.", location='headers')
    patch_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    patch_parser.add_argument("admin_username", required=False, type=str, help="If a username is given, their API key will be reset. Otherwise the user's whose API key was provided will be reset. This allows can be initiated by other instance admins or the fediseer.", location="json")
    patch_parser.add_argument("return_new_key", default=False, required=False, type=bool, help="If True, the key will be returned as part of the response instead of PM'd. IT will still PM a notification to you.", location="json")
    patch_parser.add_argument("sysadmins", default=None, required=False, type=int, help="How many sysadmins this instance has.", location="json")
    patch_parser.add_argument("moderators", default=None, required=False, type=int, help="How many moderators this instance has.", location="json")
    patch_parser.add_argument("pm_proxy", required=False, type=str, help="(Optional) If you do receive the PM from @fediseer@fediseer.com, set this to true to make the Fediseer PM your your API key via @fediseer@botsin.space. For this to work, ensure that botsin.space is not blocked in your instance and optimally follow @fediseer@botsin.space as well. If set, this will be used permanently for communication to your instance.", location="json")
    patch_parser.add_argument("visibility_endorsements", required=False, type=str, location="json")
    patch_parser.add_argument("visibility_censures", required=False, type=str, location="json")
    patch_parser.add_argument("visibility_hesitations", required=False, type=str, location="json")


    @api.expect(patch_parser,models.input_instance_modify, validate=True)
    @api.marshal_with(models.response_model_api_key_reset, code=200, description='Instances', skip_none=True)
    @api.response(401, 'Invalid API Key', models.response_model_error)
    @api.response(403, 'Access Denied', models.response_model_error)
    @api.response(404, 'Instance not claimed', models.response_model_error)
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
        requestor_instance = instance
        instance_to_reset = database.find_instance_by_domain(domain)
        changed = False
        new_key = None
        if requestor_instance != instance_to_reset and user.account != "@fediseer@fediseer.com":
            raise e.Forbidden("Only an instance admin can modify the instance")
        if self.args.sysadmins is not None and instance.sysadmins != self.args.sysadmins:
            instance.sysadmins = self.args.sysadmins
            changed = True
        if self.args.moderators is not None and instance.moderators != self.args.moderators:
            instance.moderators = self.args.moderators
            changed = True
        if self.args.pm_proxy is not None:
            if instance_to_reset is None:
                raise e.NotFound(f"Instance {domain} has not been registered yet.")
            proxy = enums.PMProxy[self.args.pm_proxy]
            if instance_to_reset.software == "lemmy" and proxy == enums.PMProxy.MASTODON:
                raise e.BadRequest("I'm sorry Dave, I can't let you do that. Lemmy is not capable of receiving mastodon PMs.")
            if instance_to_reset.pm_proxy != proxy:
                activitypub_pm.pm_new_proxy_switch(proxy,instance_to_reset.pm_proxy,instance_to_reset,user.username)
                instance_to_reset.pm_proxy = proxy
                changed = True
        if self.args.visibility_endorsements is not None:
            visibility = enums.ListVisibility[self.args.visibility_endorsements]
            if instance.visibility_endorsements != visibility:
                instance.visibility_endorsements = visibility
                changed = True
        if self.args.visibility_censures is not None:
            visibility = enums.ListVisibility[self.args.visibility_censures]
            if instance.visibility_censures != visibility:
                instance.visibility_censures = visibility
                changed = True
        if self.args.visibility_hesitations is not None:
            visibility = enums.ListVisibility[self.args.visibility_hesitations]
            if instance.visibility_hesitations != visibility:
                instance.visibility_hesitations = visibility
                changed = True
        if self.args.admin_username:
            requestor = None
            if self.args.admin_username != user.username or user.account == "@fediseer@fediseer.com":
                requestor = user.username
                instance_to_reset = database.find_instance_by_account(f"@{self.args.admin_username}@{domain}")
                if instance_to_reset is None:
                    raise e.NotFound(f"No admin '{self.args.admin_username}' found in instance {domain}. Have you remembered to claim it as that admin?")
                if instance != instance_to_reset and user.account != "@fediseer@fediseer.com":
                    raise e.BadRequest("Only other admins of the same instance or the fediseer can request API key reset for others.")
                
                instance = instance_to_reset
                user = database.find_user_by_account(f"@{self.args.admin_username}@{domain}")
            if self.args.return_new_key:
                if requestor is None:
                    requestor = f"{user.username}@{requestor_instance.domain}"
                new_key = activitypub_pm.pm_new_key_notification(
                    domain=domain, 
                    username=self.args.admin_username, 
                    software=instance.software, 
                    requestor=requestor,
                    proxy=instance.pm_proxy,
                )
            else:
                new_key = activitypub_pm.pm_new_api_key(
                    domain=domain, 
                    username=self.args.admin_username, 
                    software=instance.software, 
                    requestor=requestor,
                    proxy=instance.pm_proxy,
                )
            user.api_key = hash_api_key(new_key)
            changed = True
        db.session.commit()
        if changed is True:
            if self.args.return_new_key and new_key is not None:
                return {"message": "Changed", "new_key": new_key},200
            else:
                return {"message": "Changed"},200
        else:
            return {"message": "OK"},200

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
