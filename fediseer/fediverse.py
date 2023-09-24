import requests
from loguru import logger
from pythorhead import Lemmy
from fediseer.consts import FEDISEER_VERSION
import fediseer.exceptions as e

def get_lemmy_admins(domain,software):
    requested_lemmy = Lemmy(f"https://{domain}")
    try:
        site = requested_lemmy.site.get()
    except Exception as err:
        logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise err
    if not site:
        logger.error(f"Error retrieving {software} site info for {domain}")
        raise Exception(f"Error retrieving {software} site info for {domain}")
    return [a["person"]["name"] for a in site["admins"]]

def get_mastodon_admins(domain,software):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v2/instance")
        site_json = site.json()
        if "contact" not in site_json or "account" not in site_json["contact"] or "username" not in site_json["contact"]["account"]:
            raise Exception(f"No admin contact is specified for {domain}.")
        return [site_json["contact"]["account"]["username"]]
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_firefish_admins(domain,software):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance")
        site_json = site.json()
        if "contact_account" not in site_json or "username" not in site_json["contact_account"]:
            raise Exception(f"No admin contact is specified for {domain}.")
        return [site_json["contact_account"]["username"]]
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_misskey_admins(domain,software):
    site = None
    site_json = None
    offset = 0
    admins_found = []
    try:
        while site_json is None or len(site_json) != 0 and offset < 500:
            payload = {
                "limit": 10,
                "offset": offset,
                "sort": "+createdAt",
                "state": "alive",
                "origin": "local",
                "hostname": None
                }
            site = requests.post(f"https://{domain}/api/users", json=payload)
            site_json = site.json()
            for user_entry in site_json:
                if user_entry.get("isAdmin") is True:
                    admins_found.append(user_entry["username"])
                for role in user_entry.get("roles",[]):
                    if role.get("isAdministrator") is True:
                        admins_found.append(user_entry["username"])
            offset += 10
        if len(admins_found) == 0:
            raise Exception(f"No admin contact is specified for {domain}.")
        return admins_found
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_pleroma_admins(domain,software):
    nodeinfo = None
    try:
        nodeinfo = get_nodeinfo(domain)
        nodeinfo_json = nodeinfo.json()
        if "staffAccounts" not in nodeinfo_json or len(nodeinfo_json["staffAccounts"]) == 0:
            logger.error(f"No admin contact is specified for {domain}.")
            raise Exception(f"No admin contact is specified for {domain}.")
        admin_list = []
        for staff in nodeinfo_json["staffAccounts"]:
            admin_list.append(staff.split('/')[-1])
        return admin_list
    except Exception as err:
        if nodeinfo is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def discover_admins(domain,software):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance")
        site_json = site.json()
        # Firefish style
        if "contact_account" in site_json:
            return [site_json["contact_account"]["username"]]
        # Mastodon style
        if "contact" in site_json:
            return [site_json["contact"]["account"]["username"]]
        # Pleroma/Akkoma style
        if "email" in site_json:
            admin_username = site_json["email"].split('@',1)[0]
            return [admin_username]
        raise Exception(f"Site software '{software} does not match any of the known APIs")
    except Exception as err:
        logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_unknown_admins(domain,software):
    return []

def get_admin_for_software(software: str, domain: str):
    software_map = {
        "lemmy": get_lemmy_admins,
        "mastodon": get_mastodon_admins,
        "friendica": get_mastodon_admins,
        "pleroma": get_pleroma_admins,
        "akkoma": get_pleroma_admins,
        "misskey": get_misskey_admins,
        "firefish": get_firefish_admins,
        "iceshrimp": get_firefish_admins,
        "mitra": get_firefish_admins,
        "unknown": get_unknown_admins,
        "wildcard": get_unknown_admins,
    }
    if software not in software_map:
        return discover_admins(domain,software)
    return software_map[software](domain,software)

def get_lemmy_info(domain,software,nodeinfo):
    try:
        requested_lemmy = Lemmy(f"https://{domain}")
        site = requested_lemmy.site.get()
        if not site:
            raise Exception(f"Error encountered while polling lemmy domain. Please check it's running correctly")
        open_registrations = site["site_view"]["local_site"]["registration_mode"] == "open"
        email_verify = site["site_view"]["local_site"]["require_email_verification"]
        approval_required = site["site_view"]["local_site"]["registration_mode"] == "RequireApplication"
        has_captcha = site["site_view"]["local_site"]["captcha_enabled"]
        return software,open_registrations,approval_required,email_verify,has_captcha 
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_mastodon_info(domain,software,nodeinfo):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance",timeout=5)
        site_json = site.json()
        approval_required = site_json["approval_required"]
        if nodeinfo is None:
            raise Exception("Error retrieving nodeinfo")
        open_registrations = nodeinfo["openRegistrations"]
        email_verify = None
        has_captcha = None
        return software,open_registrations,approval_required,email_verify,has_captcha
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_pleroma_info(domain,software,nodeinfo):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance",timeout=5)
        site_json = site.json()
        approval_required = site_json["approval_required"]
        if nodeinfo is None:
            raise Exception("Error retrieving nodeinfo")
        open_registrations = nodeinfo["openRegistrations"]
        email_verify = None
        has_captcha = None
        return software,open_registrations,approval_required,email_verify,has_captcha
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_firefish_info(domain,software,nodeinfo):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance",timeout=5)
        site_json = site.json()
        approval_required = site_json["approval_required"]
        if nodeinfo is None:
            raise Exception("Error retrieving nodeinfo")
        open_registrations = nodeinfo["openRegistrations"]
        email_verify = nodeinfo["metadata"]["emailRequiredForSignup"]
        has_captcha = nodeinfo["metadata"]["enableHcaptcha"] is True or nodeinfo["metadata"]["enableRecaptcha"] is True
        return software,open_registrations,approval_required,email_verify,has_captcha
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}.")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_unknown_info(domain,software,nodeinfo):
    try:
        if nodeinfo is None:
            return software,False,None,None,None
        open_registrations = nodeinfo.get("openRegistrations", False)
        return software,open_registrations,None,None,None
    except Exception as err:
        logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def discover_info(domain,software,nodeinfo):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance")
        site_json = site.json()
        approval_required = site_json.get("approval_required")
        if nodeinfo is None:
            raise Exception("Error retrieving nodeinfo")
        open_registrations = nodeinfo.get("openRegistrations")
        # Only firefish and lemmy report the next two
        if "metadata" in nodeinfo:
            email_verify = nodeinfo["metadata"].get("emailRequiredForSignup")
            has_captcha = None
            if nodeinfo["metadata"].get("enableHcaptcha") is True or nodeinfo.get("enableRecaptcha") is True:
                has_captcha = True
        return software,open_registrations,approval_required,email_verify,has_captcha
    except Exception as err:
        logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")


def get_instance_info(domain: str, allow_unreachable=False):
    nodeinfo = get_nodeinfo(domain)
    if not nodeinfo:
        if not allow_unreachable:
            raise e.BadRequest(f"Error encountered while polling domain {domain}. Please check it's running correctly")
        else:
            software = "unknown"
            if "*" in domain:
                software = "wildcard"
    else:
        software = nodeinfo["software"]["name"]
    software_map = {
        "lemmy": get_lemmy_info,
        "mastodon": get_mastodon_info,
        "friendica": get_mastodon_info,
        "pleroma": get_pleroma_info,
        "akkoma": get_pleroma_info,
        "firefish": get_firefish_info,
        "iceshrimp": get_firefish_info,
        "mitra": get_firefish_info,
        "unknown": get_unknown_info,
        "wildcard": get_unknown_info,
    }
    if software not in software_map:
        return discover_info(domain,software,nodeinfo)
    return software_map[software](domain,software,nodeinfo)


def get_nodeinfo(domain):
    try:
        headers = {
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "User-Agent": f"Fediseer/{FEDISEER_VERSION}",
        }
        wellknown = requests.get(f"https://{domain}/.well-known/nodeinfo", headers=headers, timeout=3).json()
        headers["Sec-Fetch-Site"] = "cross-site"
        nodeinfo = requests.get(wellknown['links'][-1]['href'], headers=headers, timeout=3).json()
        return nodeinfo
    except Exception as err:
        return None

# software,open_registrations,approval_required,email_verify,has_captcha    
logger.debug(get_instance_info("lemmy.dbzer0.com"))
import sys
sys.exit()