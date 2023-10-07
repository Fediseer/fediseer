import fediseer.apis.v1.base as base
import fediseer.apis.v1.whitelist as whitelist
import fediseer.apis.v1.solicitations as solicitations
import fediseer.apis.v1.endorsements as endorsements
import fediseer.apis.v1.censures as censures
import fediseer.apis.v1.hesitations as hesitations
import fediseer.apis.v1.guarantees as guarantees
import fediseer.apis.v1.activitypub as activitypub
import fediseer.apis.v1.badges as badges
import fediseer.apis.v1.find as find
import fediseer.apis.v1.report as report
import fediseer.apis.v1.admin as admin
import fediseer.apis.v1.tags as tags
import fediseer.apis.v1.faq as faq
from fediseer.apis.v1.base import api

api.add_resource(base.Suspicions, "/instances")
api.add_resource(find.FindInstance, "/find_instance")
api.add_resource(activitypub.User, "/user/<string:username>")
api.add_resource(activitypub.Inbox, "/inbox/<string:username>")
api.add_resource(whitelist.Whitelist, "/whitelist")
api.add_resource(solicitations.Solicitations, "/solicitations")
api.add_resource(whitelist.WhitelistDomain, "/whitelist/<string:domain>")
api.add_resource(endorsements.Endorsements, "/endorsements/<string:domain>")
api.add_resource(endorsements.Approvals, "/approvals/<string:domains_csv>")
api.add_resource(censures.Censures, "/censures/<string:domain>")
api.add_resource(censures.CensuresGiven, "/censures_given/<string:domains_csv>")
api.add_resource(censures.BatchCensures, "/batch/censures")
api.add_resource(hesitations.Hesitations, "/hesitations/<string:domain>")
api.add_resource(hesitations.HesitationsGiven, "/hesitations_given/<string:domains_csv>")
api.add_resource(guarantees.Guarantors, "/guarantors/<string:domain>")
api.add_resource(guarantees.Guarantees, "/guarantees/<string:domain>")
api.add_resource(badges.GuaranteeBadge, "/badges/guarantees/<string:domain>.svg")
api.add_resource(badges.EndorsementBadge, "/badges/endorsements/<string:domain>.svg")
api.add_resource(admin.Flag, "/admin/flags/<string:domain>")
api.add_resource(tags.Tags, "/tags")
api.add_resource(faq.FAQ, "/faq")
api.add_resource(report.Report, "/reports")
