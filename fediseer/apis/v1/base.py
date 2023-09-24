import os
from flask import request
from flask_restx import Namespace, Resource, reqparse
from fediseer.flask import cache, db
from fediseer.observer import retrieve_suspicious_instances
from loguru import logger
from fediseer.classes.instance import Instance
from fediseer.database import functions as database
from fediseer import exceptions as e
from fediseer.utils import hash_api_key
from fediseer.messaging import activitypub_pm
from pythorhead import Lemmy
from fediseer.fediverse import InstanceInfo
from fediseer.limiter import limiter

api = Namespace('v1', 'API Version 1' )

from fediseer.apis.models.v1 import Models

models = Models(api)

handle_bad_request = api.errorhandler(e.BadRequest)(e.handle_bad_requests)
handle_forbidden = api.errorhandler(e.Forbidden)(e.handle_bad_requests)
handle_unauthorized = api.errorhandler(e.Unauthorized)(e.handle_bad_requests)
handle_not_found = api.errorhandler(e.NotFound)(e.handle_bad_requests)
handle_too_many_requests = api.errorhandler(e.TooManyRequests)(e.handle_bad_requests)
handle_internal_server_error = api.errorhandler(e.InternalServerError)(e.handle_bad_requests)
handle_service_unavailable = api.errorhandler(e.ServiceUnavailable)(e.handle_bad_requests)

# Used to for the flask limiter, to limit requests per url paths
def get_request_path():
    # logger.info(dir(request))
    return f"{request.remote_addr}@{request.method}@{request.path}"


class Suspicions(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("activity_suspicion", required=False, default=20, type=int, help="How many users per local post+comment to consider suspicious", location="args")
    get_parser.add_argument("active_suspicion", required=False, default=500, type=int, help="How many users per active users to consider suspicious", location="args")
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
        try:
            sus_instances = retrieve_suspicious_instances(self.args.activity_suspicion, self.args.active_suspicion)
        except Exception as err:
            raise e.ServiceUnavailable("Could not retrieve list from Fediseer Observer. Please try again later")
        if self.args.csv:
            return {"csv": ",".join([instance["domain"] for instance in sus_instances])},200
        if self.args.domains:
            return {"domains": [instance["domain"] for instance in sus_instances]},200
        return {"instances": sus_instances},200

def ensure_instance_registered(domain, allow_unreachable=False):        
    instance_info = InstanceInfo(domain,allow_unreachable=allow_unreachable)
    instance = database.find_instance_by_domain(domain)
    if instance:
        if (
            instance.software != instance_info.software or
            instance.open_registrations != instance_info.open_registrations or
            instance.approval_required != instance_info.approval_required or
            instance.email_verify != instance_info.email_verify or
            instance.has_captcha != instance_info.has_captcha
        ):
            # logger.debug(["new",instance_info.software,instance_info.open_registrations,instance_info.approval_required,instance_info.email_verify,instance_info.has_captcha])        
            # logger.debug(["old", instance.software,instance.open_registrations,instance.approval_required,instance.email_verify,instance.has_captcha])        
            logger.debug(f"Updated instance info for {domain}")
            instance.software = instance_info.software
            instance.open_registrations = instance_info.open_registrations
            instance.approval_required = instance_info.approval_required
            instance.email_verify = instance_info.email_verify
            instance.has_captcha = instance_info.has_captcha
            db.session.commit()
        
        return instance, instance_info
    new_instance = Instance(
        domain=domain,
        open_registrations=instance_info.open_registrations,
        email_verify=instance_info.email_verify,
        approval_required=instance_info.approval_required,
        has_captcha=instance_info.has_captcha,
        software=instance_info.software,
    )
    new_instance.create()
    return new_instance, instance_info

# Debug
# from fediseer.flask import OVERSEER
# with OVERSEER.app_context():
#     logger.debug(ensure_instance_registered("lemmings.world"))
#     import sys
#     sys.exit()