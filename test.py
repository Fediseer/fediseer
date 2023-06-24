import requests
import json
from datetime import datetime
import OpenSSL.crypto
import base64
import hashlib
import sys
import uuid

with open('lemmy-hello-world.json', 'r') as file:
    document = json.loads(file.read())    
document["id"] = f"https://fediseer.com/{uuid.uuid4()}"
document["object"]["id"] = f"https://fediseer.com/{uuid.uuid4()}"
document["object"]["published"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
document = json.dumps(document, indent=4)
print(document)
digest = hashlib.sha256(document.encode('utf-8')).digest()
encoded_digest = base64.b64encode(digest).decode('utf-8')
digest_header = "SHA-256=" + encoded_digest
date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

with open('private.pem', 'rb') as file:
    private_key_data = file.read()
    private_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, private_key_data)

signed_string = f"(request-target): post /inbox\nhost: overctrl.dbzer0.com\ndate: {date}\ndigest: {digest_header}"
signature = OpenSSL.crypto.sign(private_key, signed_string.encode('utf-8'), 'sha256')
encoded_signature = base64.b64encode(signature).decode('utf-8')

header = f'keyId="https://fediseer.com/api/v1/user/fediseer",headers="(request-target) host date digest",signature="{encoded_signature}"'
headers = {
    'Host': 'overctrl.dbzer0.com',
    'Date': date,
    'Signature': header,
    'Digest': digest_header,
    'Content-Type': 'application/ld+json; profile="http://www.w3.org/ns/activitystreams"'
}
url = 'https://overctrl.dbzer0.com/inbox'
response = requests.post(url, data=document, headers=headers)
print('Response Status:', response.status_code)
print('Response Body:', response.text)
