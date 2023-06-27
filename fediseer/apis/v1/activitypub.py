from fediseer.apis.v1.base import *
from fediseer.fediverse import get_nodeinfo

class User(Resource):
    get_parser = reqparse.RequestParser()

    @api.expect(get_parser)
    @cache.cached(timeout=10)
    def get(self, username):
        '''User details
        '''
        self.args = self.get_parser.parse_args()
        if username != "fediseer":
            raise e.NotFound("User does not exist")
        with open('public.pem', 'r') as file:
            pubkey = file.read()       
        fediseer = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1"
            ],
            "type": "Person",
            "id": "https://fediseer.com/api/v1/user/fediseer",
            "type": "Person",
            "preferredUsername": "fediseer",
            "inbox": "https://fediseer.com/api/v1/inbox/fediseer",
            "outbox": "https://fediseer.com/api/v1/outbox/fediseer",
            "publicKey": {
                "id": "https://fediseer.com/api/v1/user/fediseer#main-key",
                "owner": "https://fediseer.com/api/v1/user/fediseer",
                "publicKeyPem": pubkey
            }
        }
        return fediseer,200

class Inbox(Resource):
    post_parser = reqparse.RequestParser()

    @api.expect(post_parser)
    def post(self, username):
        '''User Inbox
        '''
        if username != "fediseer":
            raise e.NotFound("User does not exist")
        self.args = self.post_parser.parse_args()
        json_payload = request.get_json()
        actor = json_payload["actor"]
        if json_payload.get("type") == "Follow":
            logger.info(f"Fediseer is now followed from: {actor}")
        elif json_payload.get("type") == "Delete":
            pass
        else:
            try:
                message = json_payload["object"]["content"]
                logger.info(f"Fediseer Inbox Received: From: {actor} | {message}")
            except:
                logger.info(f"Received unexpected inbox payload: {json_payload}")
        return {"message": "delivered"}, 200
