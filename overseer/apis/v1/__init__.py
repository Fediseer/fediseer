import overseer.apis.v1.base as base
import overseer.apis.v1.endorsements as endorsements
from overseer.apis.v1.base import api

api.add_resource(base.Suspicions, "/instances")
api.add_resource(base.Whitelist, "/whitelist")
api.add_resource(base.WhitelistDomain, "/whitelist/<string:domain>")
api.add_resource(endorsements.Endorsements, "/endorsements/<string:domain>")
api.add_resource(endorsements.Approvals, "/approvals/<string:domain>")
