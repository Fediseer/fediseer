import requests
from loguru import logger
from pythorhead import Lemmy
from fediseer.consts import FEDISEER_VERSION
import fediseer.exceptions as e

class InstanceInfo():

    domain = None
    node_info = None
    instance_info = None
    admin_usernames = set()
    software = None
    open_registrations = None
    approval_required = None
    email_verify = None
    has_captcha = None
    _allow_unreachable = False
    _req_timeout = 5

    def __init__(self, domain, allow_unreachable=False, req_timeout=5):
        self.domain = domain
        self._allow_unreachable = allow_unreachable
        self._req_timeout = req_timeout
        if domain.endswith("test.dbzer0.com"):
            # Fake instances for testing chain of trust
            self.open_registrations = False
            self.approval_required = False
            self.email_verify = True
            self.has_captcha = True
            self.software = "lemmy"
            self.admin_usernames = {"db0"}
            self.node_info = InstanceInfo.get_nodeinfo("lemmy.dbzer0.com")
            self.instance_info = {}
            return

        self.node_info = InstanceInfo.get_nodeinfo(domain,req_timeout=self._req_timeout)
        try:
            self.parse_instance_info()
        except Exception as err:
            # This is just to report for the error message
            if self.software is not None:
                sw = self.software
            else:
                sw = 'unknown'
            if not self._allow_unreachable:
                logger.error(f"Error retrieving {sw} site info for {self.domain}: {err}")
                raise Exception(f"Error retrieving {sw} site info for {self.domain}: {err}")
        try:
            self.retrieve_admins()
        except:
            pass

    def get_lemmy_admins(self):
        self.admin_usernames = set([a["person"]["name"] for a in self.instance_info["admins"]])

    def get_mastodon_admins(self):
        if "contact_account" in self.instance_info: # New API
            if "username" not in self.instance_info["contact_account"]:
                raise Exception(f"No admin contact is specified for {self.domain}.")
            self.admin_usernames = {self.instance_info["contact_account"]["username"]}
        elif "contact" in self.instance_info: # Old API
            if "account" not in self.instance_info["contact"]:
                raise Exception(f"No admin contact is specified for {self.domain}.")
            self.admin_usernames = {self.instance_info["contact"]["account"]["username"]}
        else:
            raise Exception(f"Could not determine admin contacts for {self.domain}.")

    def get_misskey_admins(self):
        site_users = None
        users_json = None
        offset = 0
        admins_found = set()
        while users_json is None or len(users_json) != 0 and offset < 500:
            payload = {
                "limit": 10,
                "offset": offset,
                "sort": "+createdAt",
                "state": "alive",
                "origin": "local",
                "hostname": None
                }
            site_users = requests.post(f"https://{self.domain}/api/users", json=payload)
            users_json = site_users.json()
            for user_entry in users_json:
                if user_entry.get("isAdmin") is True:
                    admins_found.add(user_entry["username"])
                for role in user_entry.get("roles",[]):
                    if role.get("isAdministrator") is True:
                        admins_found.add(user_entry["username"])
            offset += 10
        if len(admins_found) == 0:
            raise Exception(f"No admin contact is specified for {self.domain}.")
        self.admin_usernames = admins_found

    def get_pleroma_admins(self):
        if "staffAccounts" not in self.node_info["metadata"] or len(self.node_info["metadata"]["staffAccounts"]) == 0:
            raise Exception(f"No admin contact is specified for {self.domain}.")
        for staff in self.node_info["metadata"]["staffAccounts"]:
            self.admin_usernames.add(staff.split('/')[-1])

    def discover_admins(self):
        try:
            self.get_mastodon_admins()
            return
        except:
            pass
        try:
            self.get_lemmy_admins()
            return
        except:
            pass
        try:
            self.get_pleroma_admins()
            return
        except:
            pass
        try:
            self.get_misskey_admins()
            return
        except:
            pass
        logger.warning(f"Site software '{self.software} does not match any of the known APIs")
        raise Exception(f"Site software '{self.software} does not match any of the known APIs")

    def get_unknown_admins(self):
        return []

    def retrieve_admins(self):
        software_map = {
            "lemmy": self.get_lemmy_admins,
            "mastodon": self.get_mastodon_admins,
            "friendica": self.get_mastodon_admins,
            "pleroma": self.get_pleroma_admins,
            "akkoma": self.get_pleroma_admins,
            "misskey": self.get_misskey_admins,
            "firefish": self.get_mastodon_admins,
            "iceshrimp": self.get_mastodon_admins,
            "mitra": self.get_mastodon_admins,
            "unknown": self.get_unknown_admins,
            "wildcard": self.get_unknown_admins,
        }
        if self.software not in software_map:
            self.discover_admins()
        else:
            software_map[self.software]()

    def get_lemmy_info(self):
        requested_lemmy = Lemmy(f"https://{self.domain}")
        self.instance_info = requested_lemmy.site.get()
        if not self.instance_info:
            raise Exception(f"Error encountered while polling lemmy domain. Please check it's running correctly")
        self.open_registrations = self.instance_info["site_view"]["local_site"]["registration_mode"] == "open"
        self.email_verify = self.instance_info["site_view"]["local_site"]["require_email_verification"]
        self.approval_required = self.instance_info["site_view"]["local_site"]["registration_mode"] == "RequireApplication"
        self.has_captcha = self.instance_info["site_view"]["local_site"]["captcha_enabled"]

    def get_mastodon_info(self):
        site = requests.get(f"https://{self.domain}/api/v1/instance",timeout=self._req_timeout)
        self.instance_info = site.json()
        self.approval_required = self.instance_info["approval_required"]
        if self.node_info is None:
            raise Exception("Error retrieving nodeinfo")
        self.open_registrations = self.node_info["openRegistrations"]
        self.email_verify = None
        self.has_captcha = None

    def get_pleroma_info(self):
        site = requests.get(f"https://{self.domain}/api/v1/instance",timeout=self._req_timeout)
        self.instance_info = site.json()
        self.approval_required = self.instance_info["approval_required"]
        if self.node_info is None:
            raise Exception("Error retrieving nodeinfo")
        self.open_registrations = self.node_info["openRegistrations"]
        self.email_verify = None
        self.has_captcha = None

    def get_firefish_info(self):
        site = requests.get(f"https://{self.domain}/api/v1/instance",timeout=self._req_timeout)
        self.instance_info = site.json()
        self.approval_required = self.instance_info["approval_required"]
        if self.node_info is None:
            raise Exception("Error retrieving nodeinfo")
        self.open_registrations = self.node_info["openRegistrations"]
        self.email_verify = self.node_info["metadata"]["emailRequiredForSignup"]
        self.has_captcha = self.node_info["metadata"]["enableHcaptcha"] is True or self.node_info["metadata"]["enableRecaptcha"] is True

    def get_unknown_info(self):
        if self.node_info is not None:
            self.open_registrations = self.node_info.get("openRegistrations", False)

    def discover_info(self):
        site = requests.get(f"https://{self.domain}/api/v1/instance",timeout=self._req_timeout,allow_redirects=False)
        if site.status_code != 200:
            raise Exception(f"Unexpected status code retrieved when discovering nodeinfo: {site.status_code}")
        self.instance_info = site.json()
        self.approval_required = self.instance_info.get("approval_required")
        if self.node_info is None:
            raise Exception("Error retrieving nodeinfo")
        self.open_registrations = self.node_info.get("openRegistrations")
        # Only firefish and lemmy report the next two
        if "metadata" in self.node_info:
            self.email_verify = self.node_info["metadata"].get("emailRequiredForSignup")
            self.has_captcha = None
            if self.node_info["metadata"].get("enableHcaptcha") is True or self.node_info.get("enableRecaptcha") is True:
                self.has_captcha = True


    def parse_instance_info(self):
        if not self.node_info:
            if self._allow_unreachable:
                self.software = "unknown"
                if "*" in self.domain:
                    self.software = "wildcard"
        else:
            self.software = self.node_info["software"]["name"]
        software_map = {
            "lemmy": self.get_lemmy_info,
            "mastodon": self.get_mastodon_info,
            "friendica": self.get_mastodon_info,
            "pleroma": self.get_pleroma_info,
            "akkoma": self.get_pleroma_info,
            "firefish": self.get_firefish_info,
            "iceshrimp": self.get_firefish_info,
            "mitra": self.get_firefish_info,
            "unknown": self.get_unknown_info,
            "wildcard": self.get_unknown_info,
        }
        if self.software not in software_map:
            self.discover_info()
        else:
            software_map[self.software]()

    @staticmethod
    def get_nodeinfo(domain, req_timeout=3):
        try:
            headers = {
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-GPC": "1",
                "User-Agent": f"Fediseer/{FEDISEER_VERSION}",
            }
            wellknown = requests.get(f"https://{domain}/.well-known/nodeinfo", headers=headers, timeout=req_timeout).json()
            headers["Sec-Fetch-Site"] = "cross-site"
            nodeinfo = requests.get(wellknown['links'][-1]['href'], headers=headers, timeout=req_timeout).json()
            return nodeinfo
        except Exception as err:
            return None

    @staticmethod
    def is_reachable(domain, req_timeout=5):
        # Attempts to check if we can even reach the frontpage of the domain
        # so that we know if it's an issue reaching the nodeinfo, or a problem of reaching the domain
        logger.debug(domain)
        req = requests.get(f"https://{domain}", timeout=req_timeout, allow_redirects=False)
        logger.debug(req.status_code)
        if req.status_code not in [200,401,403]:
            raise Exception(f"Status code unexpected for instance frontpage: {req.status_code}")

# Debug
# ii = InstanceInfo("lemmy.dbzer0.com")
# logger.debug([
#     ii.software,
#     ii.open_registrations,
#     ii.approval_required,
#     ii.email_verify,
#     ii.has_captcha,
#     ii.admin_usernames])
# import sys
# sys.exit()