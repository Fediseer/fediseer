import json
from overseer.observer import retrieve_suspicious_instances

sus = retrieve_suspicious_instances(20)
if sus:
    print(json.dumps([bn["domain"] for bn in sus], indent=4))