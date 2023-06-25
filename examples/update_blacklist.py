import requests

from pythorhead import Lemmy

# Your own instance's domain
LEMMY_DOMAIN = "lemmy.dbzer0.com"
USERNAME = "username"
PASSWORD = "password"
# If there's this many registered users per local post+comments, this site will be considered suspicious
ACTIVITY_SUSPICION = 20
# If there's this many registered users per active monthly user, this site will be considered suspicious
MONTHLY_ACTIVITY_SUSPICION = 500
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
sus = requests.get(f"https://fediseer.com/api/v1/instances?activity_suspicion={ACTIVITY_SUSPICION}&active_suspicion={MONTHLY_ACTIVITY_SUSPICION}domains=true", timeout=5).json()
defed = blacklist | set(sus["domains"])
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
print("Edit Successful")