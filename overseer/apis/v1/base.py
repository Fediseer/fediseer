from flask import request
from flask_restx import Namespace, Resource, reqparse
from overseer.flask import cache
from overseer.observer import retrieve_suspicious_instances
from loguru import logger

api = Namespace('v1', 'API Version 1' )

from overseer.apis.models.v1 import Models

models = Models(api)

# Used to for the flask limiter, to limit requests per url paths
def get_request_path():
    # logger.info(dir(request))
    return f"{request.remote_addr}@{request.method}@{request.path}"


class SusInstances(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("user_to_post_ratio", required=False, default=20, type=int, help="The amount of local users / amount of local posts to consider suspicious", location="args")

    @api.expect(get_parser)
    @logger.catch(reraise=True)
    @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_suspicious_instances, code=200, description='Suspicious Instances', as_list=True, skip_none=True)
    def get(self):
        '''A List with the details of all suspicious instances
        '''
        self.args = self.get_parser.parse_args()
        return retrieve_suspicious_instances(self.args.user_to_post_ratio),200

    post_parser = reqparse.RequestParser()
    post_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    post_parser.add_argument("user_to_post_ratio", required=False, default=20, type=int, help="The amount of local users / amount of local posts to consider suspicious", location="json")
    post_parser.add_argument("whitelist", type=list, required=False, help="Workers to whitelist even if we think they're suspicious", location="json")
    post_parser.add_argument("blacklist", type=list, required=False, help="Extra workers to blacklist.", location="json")

    @api.expect(post_parser, models.input_model_SusInstances_post, validate=True)
    @logger.catch(reraise=True)
    # @cache.cached(timeout=10, query_string=True)
    @api.marshal_with(models.response_model_model_SusInstances_post, code=200, description='Suspicious Instances List')
    @api.response(400, 'Validation Error', models.response_model_error)
    def post(self):
        '''A List with just the domains of all suspicious instances
        This can then be easily converted into a defederation list
        '''
        self.args = self.post_parser.parse_args()
        logger.debug(self.args)
        sus_instances = retrieve_suspicious_instances(self.args.user_to_post_ratio)
        final_list = []
        if self.args.blacklist:
            final_list = self.args.blacklist
        whitelist = []
        if self.args.whitelist:
            whitelist = self.args.whitelist
        for instance in sus_instances:
            if instance["domain"] not in whitelist:
                final_list.append(instance["domain"])
        return {"domains": final_list},200
