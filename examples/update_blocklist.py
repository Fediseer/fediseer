import os
import json
import sys
from dotenv import load_dotenv
from pythorhead import Lemmy
from pythonseer import Fediseer
from pythonseer.types import FormatType

load_dotenv()
# Your own instance's domain
LEMMY_DOMAIN = "lemmy.dbzer0.com"
USERNAME = "username"
# You can write your password here, or add it to the LEMMY_PASSWORD env var, or add LEMMY_PASSWORD to a .env file
PASSWORD = "password"
# If there's this many registered users per local post+comments, this site will be considered suspicious
ACTIVITY_SUSPICION = 20
# If there's this many registered users per active monthly user, this site will be considered suspicious
MONTHLY_ACTIVITY_SUSPICION = 500
# Extra domains you can block. You can just delete the contents if you want to only block suspicious domains
blocklist = [
    "truthsocial.com",
    "threads.net",
]
# Add instances in here which want to ensure are not added in your blocklist
# 
safelist = [
]
# If you (don't) want to combine your own censures, with the ones from other trusted instances, adjust the list below.
# The censures will be the combined list from your own domain and any domains specified below.
trusted_instances = [
    "lemmy.world"
]
# If you want to only block based on specific filters as specified by the admins who have censured them
# You can provide them in a list below. Any instance marked with that filter from your trusted instances
# Will be added. Others will be ignored
# Sample has been provided below
filtered_instances = [
    "lemmings.world",
]
reason_filters = [
    "__all_pedos__",
    "__all_bigots__",
]
# If you want to only censure instances which have been marked by more than 1 trusted instance, then increase the number below
min_censures = 1
# Change this to the number of changes over which this script will ask for manual confirmation
changes_warning_threshold = 10

password = os.getenv("LEMMY_PASSWORD", PASSWORD)
lemmy = Lemmy(f"https://{LEMMY_DOMAIN}", request_timeout=15)
if lemmy.log_in(USERNAME, password) is False:
    raise Exception("Could not log in to lemmy")

fediseer = Fediseer()
print("Fetching suspicions")
sus = fediseer.suspicions.get(
    activity_suspicion=ACTIVITY_SUSPICION,
    active_suspicion=MONTHLY_ACTIVITY_SUSPICION,
    format=FormatType.LIST
)
print("Fetching trusted censures")
trusted_instances.append(LEMMY_DOMAIN)
trusted_censures = fediseer.censure.get_given(
    domain_set = set(trusted_instances), 
    min_censures = min_censures, 
    format = FormatType.LIST,
)
print("Fetching filtered censures")
filtered_censures = fediseer.censure.get_given(
    domain_set = set(filtered_instances), 
    reasons = reason_filters, 
    min_censures = min_censures, 
    format = FormatType.LIST,
)
print("Fetching endorsements")
trusted_instances.append(LEMMY_DOMAIN)
endorsements = fediseer.endorsement.get_given(
    domain_set = set(trusted_instances), 
    format = FormatType.LIST,
)
defed = (set(blocklist) | set(trusted_censures["domains"]) | set(filtered_censures["domains"]) | set(sus["domains"])) - set(safelist) - set(endorsements["domains"])
try:
    with open("previous_defed.json", 'r') as file:
        prev_defed = set(json.loads(file.read()))
except (FileNotFoundError,json.decoder.JSONDecodeError):
    print("WARNING: Previous defed file doesn't exist. Will probably receive a warning about blocklist.")
    prev_defed = set()
if len(defed - prev_defed) > 0:
    print(f"New blocks to add {defed - prev_defed}")
if len(prev_defed - defed) > 0:
    print(f"blocks that will be removed {prev_defed - defed}")
if len(defed - prev_defed) + len(prev_defed - defed) == 0:
    print("No changes to do in blocklist")
    sys.exit()
if len(defed - prev_defed) + len(prev_defed - defed) >= changes_warning_threshold:
    if input(
        f"\n### WARNING ###\n"
        f"You are about to do {changes_warning_threshold} of more changes to your blocklist. "
        "Proceed? (Y/n)",
    ) not in ["y", "Y", "", "yes"]:
        print("Aborting run")
        sys.exit()
# I need to retrieve the site info because it seems if "RequireApplication" is set
# We need to always re-set the application_question.
# So we retrieve it from the existing site, to set the same value
site = lemmy.site.get()
application_question = None
if site["site_view"]["local_site"]["registration_mode"] == "RequireApplication":
    application_question = site["site_view"]["local_site"]["application_question"]
print("Editing Defederation list")
if application_question:
    ret = lemmy.site.edit(
        blocked_instances=list(defed),
        application_question=application_question,
        )
else:
    ret = lemmy.site.edit(
        blocked_instances=list(defed),
        )
if ret is None:
    print("Edit Failed!")
else:    
    print("Edit Successful.")
    with open("previous_defed.json", 'w') as file:
        file.write(json.dumps(list(defed),indent=4))
    print("Stored previous defed list to disk file 'previous_defed.json'")
