import overseer.apis.v1.base as base
import overseer.apis.v1.whitelist as whitelist
import overseer.apis.v1.endorsements as endorsements
import overseer.apis.v1.guarantees as guarantees
from overseer.apis.v1.base import api

api.add_resource(base.Suspicions, "/instances")
api.add_resource(whitelist.Whitelist, "/whitelist")
api.add_resource(whitelist.WhitelistDomain, "/whitelist/<string:domain>")
api.add_resource(endorsements.Endorsements, "/endorsements/<string:domain>")
api.add_resource(endorsements.Approvals, "/approvals/<string:domain>")
api.add_resource(guarantees.Guarantors, "/guarantors/<string:domain>")
api.add_resource(guarantees.Guarantees, "/guarantees/<string:domain>")
