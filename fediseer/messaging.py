import requests
import json
from datetime import datetime
import OpenSSL.crypto
import base64
import hashlib
import uuid
import copy
import os
import secrets
import markdown
import fediseer.exceptions as e
from pythorhead import Lemmy
from loguru import logger
from fediseer.database import functions as database
from fediseer.consts import SUPPORTED_SOFTWARE, FEDISEER_VERSION
from fediseer.fediverse import get_admin_for_software

class ActivityPubPM:
    private_key = None
    def __init__(self):
        with open('private.pem', 'rb') as file:
            private_key_data = file.read()
            self.private_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, private_key_data)
        self.document_core = {
            "type": "Create",
            "actor": "https://fediseer.com/api/v1/user/fediseer",
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https: //w3id.org/security/v1"
            ],	
            "object": {
                "attributedTo": "https://fediseer.com/api/v1/user/fediseer",
            },
        }

    def send_pm_to_right_software(self, message, username, domain, software):
        software_map = {
            "lemmy": self.send_lemmy_pm,
            "mastodon": self.send_mastodon_pm,
            "friendica": self.send_mastodon_pm,
            "fediseer": self.send_fediseer_pm,
        }
        return software_map[software](message, username, domain)

    def send_fediseer_pm(self, message, username, domain):
        document = copy.deepcopy(self.document_core)
        document["to"] =  [f"https://lemmy.dbzer0.com/u/db0"]
        document["object"]["content"] = markdown.markdown(message)
        document["object"]["type"] = "ChatMessage"
        document["object"]["mediaType"] = "text/html"
        document["object"]["to"] = [f"https://lemmy.dbzer0.com/u/db0"]
        document["object"]["source"] =  {
            "content": message,
            "mediaType": "text/markdown",
        }
        return self.send_pm(document, domain)

    def send_lemmy_pm(self, message, username, domain):
        document = copy.deepcopy(self.document_core)
        document["to"] =  [f"https://{domain}/u/{username}"]
        document["object"]["content"] = markdown.markdown(message)
        document["object"]["type"] = "ChatMessage"
        document["object"]["mediaType"] = "text/html"
        document["object"]["to"] = [f"https://{domain}/u/{username}"]
        document["object"]["source"] =  {
            "content": message,
            "mediaType": "text/markdown",
        }
        return self.send_pm(document, domain)

    def send_mastodon_pm(self, message, username, domain):
        document = copy.deepcopy(self.document_core)
        document["object"]["content"] = markdown.markdown(message)
        document["object"]["type"] = "Note"
        document["object"]["to"] = f"https://{domain}/users/{username}"
        document["object"]["tag"] = [
			{
			  "type": "Mention",
			  "to": f"@{username}",
			  "href": f"https://{domain}/users/{username}"
			}
		]
        return self.send_pm(document, domain)

    def send_pm(self, document, domain):
        document["id"] = f"https://fediseer.com/{uuid.uuid4()}"
        document["object"]["id"] = f"https://fediseer.com/{uuid.uuid4()}"
        document["object"]["published"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        document = json.dumps(document, indent=4)
        digest = hashlib.sha256(document.encode('utf-8')).digest()
        encoded_digest = base64.b64encode(digest).decode('utf-8')
        digest_header = "SHA-256=" + encoded_digest
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        signed_string = f"(request-target): post /inbox\nhost: {domain}\ndate: {date}\ndigest: {digest_header}"
        signature = OpenSSL.crypto.sign(self.private_key, signed_string.encode('utf-8'), 'sha256')
        encoded_signature = base64.b64encode(signature).decode('utf-8')

        header = f'keyId="https://fediseer.com/api/v1/user/fediseer",headers="(request-target) host date digest",signature="{encoded_signature}"'
        headers = {
            'Host': domain,
            'Date': date,
            'Signature': header,
            'Digest': digest_header,
            'Content-Type': 'application/ld+json; profile="http://www.w3.org/ns/activitystreams"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "User-Agent": f"Fediseer/{FEDISEER_VERSION}",
        }
        url = f"https://{domain}/inbox"
        response = requests.post(url, data=document, headers=headers)
        return response.ok

    def pm_new_api_key(self, domain: str, username: str, software: str, requestor = None):
        api_key = secrets.token_urlsafe(16)
        if requestor:
            pm_content = f"user '{requestor}' has initiated an API Key reset for your domain {domain} on the [Fediseer](https://fediseer.com)\n\nThe new API key is\n\n{api_key}\n\n**Please purge this message after storing the API key**"
        else:
            pm_content = f"Your API Key for domain {domain} is\n\n{api_key}\n\nUse this to perform operations on the [Fediseer](https://fediseer.com).\n\n**Please purge this message after storing the API key**"
        if not self.send_pm_to_right_software(
            message=pm_content,
            username=username,
            domain=domain,
            software=software
        ):
            raise e.BadRequest("API Key PM failed")
        return api_key

    def pm_new_key_notification(self, domain: str, username: str, software: str, requestor: str):
        api_key = secrets.token_urlsafe(16)
        pm_content = f"user '{requestor}' has initiated an API Key reset for your domain {domain} on the [Fediseer](https://fediseer.com)\n\nThe new API key was provided in the response already\n"
        logger.info(f"user '{requestor}' reset the API key for {username}@{domain} on the response.")
        if not self.send_pm_to_right_software(
            message=pm_content,
            username=username,
            domain=domain,
            software=software
        ):
            raise e.BadRequest("API Key PM failed")
        return api_key


    def pm_admins(self, message: str, domain: str, software: str, instance):
        if software not in SUPPORTED_SOFTWARE:
            return None
        admins = database.find_admins_by_instance(instance)
        if not admins:
            admins = get_admin_for_software(software, domain)
        else:
            admins = [a.username for a in admins]
        if not admins:
            raise e.BadRequest(f"Could not determine admins for {domain}")
        for admin_username in admins:
            if not self.send_pm_to_right_software(
                message=message,
                username=admin_username,
                domain=domain,
                software=software
            ):
                raise e.BadRequest("Admin PM Failed")


activitypub_pm = ActivityPubPM()
