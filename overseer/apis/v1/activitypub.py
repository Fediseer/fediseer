from overseer.apis.v1.base import *
from overseer.utils import get_nodeinfo

class User(Resource):
    get_parser = reqparse.RequestParser()

    @api.expect(get_parser)
    @cache.cached(timeout=10)
    def get(self, username):
        '''User details
        '''
        self.args = self.get_parser.parse_args()
        if username != "overseer":
            raise e.NotFound("User does not exist")
        with open('public.pem', 'r') as file:
            pubkey = file.read()       
        overseer = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1"
            ],

            "id": "https://overseer.dbzer0.com/api/v1/user/overseer",
            "type": "Person",
            "preferredUsername": "overseer",
            "inbox": "https://overseer.dbzer0.com/api/v1/inbox/overseer",

            "publicKey": {
                "id": "https://overseer.dbzer0.com/api/v1/user/overseer#main-key",
                "owner": "https://overseer.dbzer0.com/api/v1/user/overseer",
                "publicKeyPem": pubkey
            }
        }
        return overseer,200

class Inbox(Resource):
    post_parser = reqparse.RequestParser()

    @api.expect(post_parser)
    def post(self, username):
        '''User Inbox
        '''
        if username != "overseer":
            raise e.NotFound("User does not exist")
        self.args = self.post_parser.parse_args()
        json_payload = request.get_json()
        print(json_payload)
        print("inbox hit")
        return {"message": "delivered"}, 200
