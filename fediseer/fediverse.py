import requests
from loguru import logger
from pythorhead import Lemmy
from fediseer.consts import FEDISEER_VERSION

def get_lemmy_admins(domain):
    requested_lemmy = Lemmy(f"https://{domain}")
    site = requested_lemmy.site.get()
    if not site:
        logger.warning(f"Error retrieving mastodon site info for {domain}")
        raise Exception(f"Error retrieving mastodon site info for {domain}")
    return [a["person"]["name"] for a in site["admins"]]

def get_mastodon_admins(domain):
    try:
        site = requests.get(f"https://{domain}/api/v2/instance").json()
        return [site["contact"]["account"]["username"]]
    except Exception as err:
        logger.warning(f"Error retrieving mastodon site info for {domain}: {err}")
        raise Exception(f"Error retrieving mastodon site info for {domain}: {err}")

def get_unknown_admins(domain):
    return []

def get_admin_for_software(software: str, domain: str):
    software_map = {
        "lemmy": get_lemmy_admins,
        "mastodon": get_mastodon_admins,
        "friendica": get_mastodon_admins,
        "unknown": get_unknown_admins,
        "wildcard": get_unknown_admins,
    }
    if software not in software_map:
        return []
    return software_map[software](domain)


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