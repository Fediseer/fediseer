import requests
from loguru import logger
from pythorhead import Lemmy
from fediseer.consts import FEDISEER_VERSION

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
            logger.error(f"No admin contact is specified for {domain}.")
            raise Exception(f"No admin contact is specified for {domain}.")
        return [site_json["contact"]["account"]["username"]]
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}. Request text: {site.text()}")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_misskey_admins(domain,software):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance")
        site_json = site.json()
        if "contact_account" not in site_json or "username" not in site_json["contact_account"]:
            logger.error(f"No admin contact is specified for {domain}.")
            raise Exception(f"No admin contact is specified for {domain}.")
        return [site_json["contact_account"]["username"]]
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}. Request text: {site.text()}")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def get_pleroma_admins(domain,software):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance")
        site_json = site.json()
        if "email" not in site_json or site_json["email"] is None or site_json["email"] == '':
            logger.error(f"No admin contact is specified for {domain}.")
            raise Exception(f"No admin contact is specified for {domain}.")
        admin_username = site_json["email"].split('@',1)[0]
        return [admin_username]
    except Exception as err:
        if site is not None:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}. Request text: {site.text()}")
        else:
            logger.error(f"Error retrieving {software} site info for {domain}: {err}")
        raise Exception(f"Error retrieving {software} site info for {domain}: {err}")

def discover_admins(domain,software):
    site = None
    try:
        site = requests.get(f"https://{domain}/api/v1/instance")
        site_json = site.json()
        # Pleroma/Akkoma style
        if "email" in site_json:
            admin_username = site_json["email"].split('@',1)[0]
            return [admin_username]
        # Misskey/Firefish style
        if "contact_account" in site_json:
            return [site_json["contact_account"]["username"]]
        # Mastodon style
        if "contact" in site_json:
            return [site_json["contact"]["account"]["username"]]
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
        "firefish": get_misskey_admins,
        "iceshrimp": get_misskey_admins,
        "mitra": get_misskey_admins,
        "misskey": get_misskey_admins,
        "unknown": get_unknown_admins,
        "wildcard": get_unknown_admins,
    }
    if software not in software_map:
        return discover_admins(domain,software)
    return software_map[software](domain,software)


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