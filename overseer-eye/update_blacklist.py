import requests
import os
from pythorhead import Lemmy

LEMMY_DOMAIN = os.getenv('LEMMY_DOMAIN')
OVERSEER_DOMAIN = os.getenv('OVERSEER_DOMAIN', 'overseer.dbzer0.com')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
# If there's this many registered users per local post+comments, this site will be considered suspicious
ACTIVITY_SUSPICION = os.getenv('ACTIVITY_SUSPICION', '20')
# Extra domains you can block. You can just delete the contents if you want to only block suspicious domains
blacklistString = os.getenv('ACTIVITY_SUSPICION', "truthsocial.com, exploding-heads.com, lemmygrad.ml")
blacklist = [x.strip() for x in blacklistString.split(',')]


lemmy = Lemmy(f"https://{LEMMY_DOMAIN}")
if lemmy.log_in(USERNAME, PASSWORD) is False:
    raise Exception("Could not log in to lemmy")

print("Fetching suspicions")
sus = requests.get(f"https://{OVERSEER_DOMAIN}/api/v1/instances?activity_suspicion={ACTIVITY_SUSPICION}&domains=true", timeout=5).json()
defed = blacklist | set(sus("domains"))
print("Editing Defederation list")
ret = lemmy.site.edit(blocked_instances=list(defed))
print("Edit Successful")