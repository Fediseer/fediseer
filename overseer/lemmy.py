from pythorhead import Lemmy
from loguru import logger
import os
import secrets
import overseer.exceptions as e

overctrl_lemmy = Lemmy(f"https://{os.getenv('FEDISEER_LEMMY_DOMAIN')}")
_login = overctrl_lemmy.log_in(os.getenv('FEDISEER_LEMMY_USERNAME'),os.getenv('FEDISEER_LEMMY_PASSWORD'))
if not _login:
    raise Exception("Failed to login to overctrl")
overseer_lemmy_user = overctrl_lemmy.user.get(username=os.getenv('FEDISEER_LEMMY_USERNAME'))

def pm_instance(domain: str, message: str):
    domain_username = domain.replace(".", "_")
    domain_user = overctrl_lemmy.user.get(username=domain_username)
    if not domain_user:
        raise e.BadRequest(f"Could not find domain user '{domain_username}'")
    pm = overctrl_lemmy.private_message(message,domain_user["person_view"]["person"]["id"])
    return pm

def pm_new_api_key(domain: str):
    api_key = secrets.token_urlsafe(16)
    pm_content = f"The API Key for domain {domain} is\n\n{api_key}\n\nUse this to perform operations on the overseer."
    if not pm_instance(domain, pm_content):
        raise e.BadRequest("API Key PM failed")
    return api_key
