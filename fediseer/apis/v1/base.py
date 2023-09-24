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
from fediseer.fediverse import get_admin_for_software, get_nodeinfo, get_instance_info
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
    if domain.endswith("test.dbzer0.com"):
        # Fake instances for testing chain of trust
        requested_lemmy = Lemmy(f"https://{domain}")
        requested_lemmy._requestor.nodeinfo = {"software":{"name":"lemmy"}}
        open_registrations = False
        email_verify = True
        has_captcha = True
        software = "lemmy"
        admin_usernames = ["db0"]
        nodeinfo = get_nodeinfo("lemmy.dbzer0.com")
        requested_lemmy = Lemmy(f"https://{domain}")
    else:
        software,open_registrations,approval_required,email_verify,has_captcha = get_instance_info(domain,allow_unreachable)
        try:
            admin_usernames = get_admin_for_software(software, domain)
        except:
            admin_usernames = []
    instance = database.find_instance_by_domain(domain)
    if instance:
        if (
            instance.software != software or
            instance.open_registrations != open_registrations or
            instance.approval_required != approval_required or
            instance.email_verify != email_verify or
            instance.has_captcha != has_captcha
        ):
            logger.debug(["would change",software,open_registrations,approval_required,email_verify,has_captcha])        
            # instance.software = software
            # instance.open_registrations = open_registrations
            # instance.approval_required = approval_required
            # instance.email_verify = email_verify
            # instance.has_captcha = has_captcha
            # db.session.commit()
        logger.debug([software,open_registrations,approval_required,email_verify,has_captcha])        
        return instance, nodeinfo, admin_usernames
    new_instance = Instance(
        domain=domain,
        open_registrations=open_registrations,
        email_verify=email_verify,
        approval_required=approval_required,
        has_captcha=has_captcha,
        software=software,
    )
    new_instance.create()
    return new_instance, nodeinfo, admin_usernames

from fediseer.flask import OVERSEER
with OVERSEER.app_context():
    logger.debug(ensure_instance_registered("lemmy.dbzer0.com"))
    import sys
    sys.exit()