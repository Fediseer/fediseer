import requests
from loguru import logger
from pythorhead import Lemmy

def get_lemmy_admins(domain):
    requested_lemmy = Lemmy(f"https://{domain}")
    site = requested_lemmy.site.get()
    if not site:
        logger.warning(f"Error retrieving mastodon site info for {domain}")
        return None
    return [a["person"]["name"] for a in site["admins"]]

def get_mastodon_admins(domain):
    try:
        site = requests(f"https://{domain}/api/v2/instance").json()
        return [site["contact"]["account"]["username"]]
    except Exception as err:
        logger.warning(f"Error retrieving mastodon site info for {domain}")
        return None

def get_admin_for_software(software: str, domain: str):
    software_map = {
        "lemmy": get_lemmy_admins,
        "mastodon": get_mastodon_admins,
    }
    if software not in software_map:
        return None
    return software_map[software](domain)


def get_nodeinfo(domain):
    try:
        headers = {
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "User-Agent": "Fediseer/0.5",
        }
        wellknown = requests.get(f"https://{domain}/.well-known/nodeinfo", headers=headers, timeout=4).json()
        headers["Sec-Fetch-Site"] = "cross-site"
        nodeinfo = requests.get(wellknown['links'][0]['href'], headers=headers, timeout=2).json()
        return nodeinfo
    except Exception as err:
        logger.debug(err)
        return None