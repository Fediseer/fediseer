from fediseer.flask import OVERSEER, db
from fediseer.database import functions as database
from fediseer.logger import logger
from fediseer.classes.instance import Instance, Endorsement, Guarantee, RejectionRecord, Censure, Hesitation, Solicitation, InstanceFlag, InstanceTag, Rebuttal
from sqlalchemy import func
import sys

## Limits test
# with OVERSEER.app_context():
#     domains_list = ["lemmy.dbzer0.com","lemmy.ca","lemmy.basedcount.com","sh.itjust.works","aussie.zone","literature.cafe","lemmy.blahaj.zone","feddit.de","lemmy.myserv.one","programming.dev","lemmy.world","lemy.lol","lemm.ee","lemmy.team","infosec.pub","discuss.tchncs.de","lemmy.zip","phpc.social","discuss.online","lemmy.magnor.ovh","lemmynsfw.com","lemmyf.uk","lemmy.cwagner.me","startrek.website","lemdro.id"]
#     instances = database.find_multiple_instance_by_domains(domains_list)
#     censures = database.get_all_censured_instances_by_censuring_id(
#         censuring_ids = [instance.id for instance in instances], limit=1000)
## Convert uppercased domains to lowercase
# with OVERSEER.app_context():
#     instances = Instance.query.filter(Instance.domain != func.lower(Instance.domain)).all()
#     for inst in instances:
#         lcinst = database.find_instance_by_domain(inst.domain.lower())
#         if not lcinst:
#             print(f"Renamed: {inst.domain}")
#             inst.domain = inst.domain.lower()
#             db.session.commit()
#             continue
#         for approval in inst.approvals:
#             print(f"Converting approval {approval.id} from: {inst.domain} to {lcinst.domain}")
#             approval.approving_instance = lcinst
#         for endorsement in inst.endorsements:
#             print(f"Converting endorsement {endorsement.id} from: {inst.domain} to {lcinst.domain}")
#             endorsement.endorsed_instance = lcinst
#         for c in inst.censures_given:
#             print(f"Converting censure_given {c.id} from: {inst.domain} to {lcinst.domain}")
#             c.censuring_instance = lcinst
#         for c in inst.censures_received:
#             print(f"Converting censure_received {c.id} from: {inst.domain} to {lcinst.domain}")
#             c.censured_instance = lcinst
#         for h in inst.hesitations_given:
#             print(f"Converting hesitation_given {h.id} from: {inst.domain} to {lcinst.domain}")
#             h.hesitating_instance = lcinst
#         for h in inst.hesitations_received:
#             print(f"Converting hesitation_received {h.id} from: {inst.domain} to {lcinst.domain}")
#             h.dubious_instance = lcinst
#         for r in inst.rebuttals_given:
#             print(f"Converting rebuttal_given {r.id} from: {inst.domain} to {lcinst.domain}")
#             h.source_instance = lcinst
#         for r in inst.rebuttals_received:
#             print(f"Converting rebuttal_received {r.id} from: {inst.domain} to {lcinst.domain}")
#             r.target_instance = lcinst
#         for g in inst.guarantees:
#             print(f"Converting guarantee {g.id} from: {inst.domain} to {lcinst.domain}")
#             g.guarantor_instance = lcinst
#         for g in inst.guarantors:
#             print(f"Converting guarantor {g.id} from: {inst.domain} to {lcinst.domain}")
#             g.guaranteed_instance = lcinst
#         print(f"deleting obsolete instance: {inst.domain}")
#         db.session.delete(inst)
#         db.session.commit()
#     print([i.domain for  i in instances])
sys.exit()
