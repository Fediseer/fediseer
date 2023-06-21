import requests

from pythorhead import Lemmy

# Your own instance's domain
LEMMY_DOMAIN = "lemmy.dbzer0.com"
USERNAME = "username"
PASSWORD = "password"
# If there's this many registered users per local post+comments, this site will be considered suspicious
ACTIVITY_SUSPICION = 20
# Extra domains you can block. You can just delete the contents if you want to only block suspicious domains
blacklist = {
    "truthsocial.com",
    "exploding-heads.com",
    "lemmygrad.ml",
}


lemmy = Lemmy(f"https://{LEMMY_DOMAIN}")
if lemmy.log_in(USERNAME, PASSWORD) is False:
    raise Exception("Could not log in to lemmy")

print("Fetching suspicions")
sus = requests.get(f"https://overseer.dbzer0.com/api/v1/instances?activity_suspicion={ACTIVITY_SUSPICION}&domains=true", timeout=5).json()
defed = blacklist | set(sus["domains"])
print("Editing Defederation list")
ret = lemmy.site.edit(blocked_instances=list(defed))
print("Edit Successful")