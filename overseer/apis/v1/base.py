import os
from flask import request
from flask_restx import Namespace, Resource, reqparse
from overseer.flask import cache, db
from overseer.observer import retrieve_suspicious_instances
from loguru import logger
from overseer.classes.instance import Instance
from overseer.database import functions as database
from overseer import exceptions as e
from overseer.utils import hash_api_key
from overseer.lemmy import pm_new_api_key
from pythorhead import Lemmy

api = Namespace('v1', 'API Version 1' )

from overseer.apis.models.v1 import Models

models = Models(api)

handle_bad_request = api.errorhandler(e.BadRequest)(e.handle_bad_requests)
handle_forbidden = api.errorhandler(e.Forbidden)(e.handle_bad_requests)
handle_unauthorized = api.errorhandler(e.Unauthorized)(e.handle_bad_requests)
handle_not_found = api.errorhandler(e.NotFound)(e.handle_bad_requests)

# Used to for the flask limiter, to limit requests per url paths
def get_request_path():
    # logger.info(dir(request))
    return f"{request.remote_addr}@{request.method}@{request.path}"


class Suspicions(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("activity_suspicion", required=False, default=20, type=int, help="How many users per local post+comment to consider suspicious", location="args")
    get_parser.add_argument("csv", required=False, type=bool, help="Set to true to return just the domains as a csv. Mutually exclusive with domains", location="args")
    get_parser.add_argument("domains", required=False, type=bool, help="Set to true to return just the domains as a list. Mutually exclusive with csv", location="args")

    @api.expect(get_parser)
    @logger.catch(reraise=True)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_Suspicions_get, code=200, description='Suspicious Instances', skip_none=True)
    def get(self):
        '''A List with the details of all suspicious instances
        '''
        self.args = self.get_parser.parse_args()
        sus_instances = retrieve_suspicious_instances(self.args.activity_suspicion)
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in sus_instances])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in sus_instances]},200
        return {"instances": sus_instances},200


class Whitelist(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("endorsements", required=False, default=1, type=int, help="Limit to this amount of endorsements of more", location="args")
    get_parser.add_argument("domain", required=False, type=str, help="Filter by instance domain", location="args")
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
        for instance in database.get_all_instances():
            instance_details.append(instance.get_details())
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in instance_details])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in instance_details]},200
        return {"instances": instance_details},200


    put_parser = reqparse.RequestParser()
    put_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    put_parser.add_argument("domain", required=False, type=str, help="The instance domain. It MUST be alredy registered in https://overctrl.dbzer0.com", location="json")
    put_parser.add_argument("guarantor", required=False, type=str, help="(Optiona) The domain of the guaranteeing instance. They will receive a PM to validate you", location="json")


    @api.expect(put_parser)
    @api.marshal_with(models.response_model_instances, code=200, description='Instances')
    def put(self):
        '''Register a new instance to the overseer
        An instance account has to exist in the overseer lemmy instance
        That account will recieve the new API key via PM
        '''
        self.args = self.put_parser.parse_args()
        existing_instance = Instance.query.filter_by(domain=self.args.domain).first()
        if existing_instance:
            return existing_instance.get_details(),200
        requested_lemmy = Lemmy(f"https://{self.args.domain}")
        site = requested_lemmy.site.get()
        api_key = pm_new_api_key(self.args.domain)
        if not api_key:
            raise e.BadRequest("Failed to generate API Key")
        new_instance = Instance(
            domain=self.args.domain,
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
    patch_parser.add_argument("domain", required=False, type=str, help="The instance domain. It MUST be alredy registered in https://overctrl.dbzer0.com", location="json")
    patch_parser.add_argument("regenerate_key", required=False, type=bool, help="If True, will PM a new api key to this instance", location="json")


    @api.expect(patch_parser)
    @api.marshal_with(models.response_model_instances, code=200, description='Instances', skip_none=True)
    def patch(self):
        '''Regenerate API key for instance
        '''
        self.args = self.patch_parser.parse_args()
        if not self.args.apikey:
            raise e.Unauthorized("You must provide the API key that was PM'd to your overctrl.dbzer0.com account")
        instance = database.find_authenticated_instance(self.args.domain, self.args.apikey)
        if not instance:
            raise e.BadRequest(f"No Instance found matching provided API key and domain. Have you remembered to register it?")
        if self.args.regenerate_key:
            new_key = pm_new_api_key(self.args.domain)
            instance.api_key = hash_api_key(new_key)
            db.session.commit()
        return instance.get_details(),200
