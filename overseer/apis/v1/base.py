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