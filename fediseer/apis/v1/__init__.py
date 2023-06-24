import fediseer.apis.v1.base as base
import fediseer.apis.v1.whitelist as whitelist
import fediseer.apis.v1.endorsements as endorsements
import fediseer.apis.v1.guarantees as guarantees
import fediseer.apis.v1.activitypub as activitypub
from fediseer.apis.v1.base import api

api.add_resource(base.Suspicions, "/instances")
api.add_resource(activitypub.User, "/user/<string:username>")
api.add_resource(activitypub.Inbox, "/inbox/<string:username>")
api.add_resource(whitelist.Whitelist, "/whitelist")
api.add_resource(whitelist.WhitelistDomain, "/whitelist/<string:domain>")
api.add_resource(endorsements.Endorsements, "/endorsements/<string:domain>")
api.add_resource(endorsements.Approvals, "/approvals/<string:domain>")
api.add_resource(guarantees.Guarantors, "/guarantors/<string:domain>")
api.add_resource(guarantees.Guarantees, "/guarantees/<string:domain>")
