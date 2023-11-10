from fediseer.flask import OVERSEER
from fediseer.database import functions as database
from fediseer.logger import logger
import sys

# Limits test
# with OVERSEER.app_context():
#     domains_list = ["lemmy.dbzer0.com","lemmy.ca","lemmy.basedcount.com","sh.itjust.works","aussie.zone","literature.cafe","lemmy.blahaj.zone","feddit.de","lemmy.myserv.one","programming.dev","lemmy.world","lemy.lol","lemm.ee","lemmy.team","infosec.pub","discuss.tchncs.de","lemmy.zip","phpc.social","discuss.online","lemmy.magnor.ovh","lemmynsfw.com","lemmyf.uk","lemmy.cwagner.me","startrek.website","lemdro.id"]
#     instances = database.find_multiple_instance_by_domains(domains_list)
#     censures = database.get_all_censured_instances_by_censuring_id(
#         censuring_ids = [instance.id for instance in instances], limit=1000)
sys.exit()
