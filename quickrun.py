import requests
import json

# GraphQL query
query = '''
{
  nodes(softwarename: "lemmy") {
    domain
    name
    metatitle
    metadescription
    metaimage
    date_created
    uptime_alltime
    total_users
    active_users_monthly
    active_users_halfyear
    signup
    local_posts
  }
}
'''

# GraphQL endpoint URL
url = 'https://api.fediverse.observer/'

# Request headers
headers = {
    'User-Agent': 'Lemmy Overseer / mail@dbzer0.com',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://api.fediverse.observer/',
    'Content-Type': 'application/json',
    'Origin': 'https://api.fediverse.observer',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers'
}

# Create the request payload
payload = {
    'query': query
}

# Send the POST request to the GraphQL endpoint
response = requests.post(url, headers=headers, json=payload)

# Check if the request was successful (HTTP 200 status code)
if response.ok:
    # Extract the JSON response
    data = response.json()
    bad_nodes = []
    for node in data["data"]["nodes"]:
        is_bad = False
        local_posts = node["local_posts"]
        if node["total_users"] < 300:
            continue
        if local_posts == 0:
            local_posts= 1
        if node["total_users"] / local_posts > 20:
            is_bad = True
            # print(node)
        if is_bad:
            bad_node = {
                "domain": node["domain"],
                "uptime_alltime": node["uptime_alltime"],
                "local_posts": node["local_posts"],
                "total_users": node["total_users"],
                "active_users_monthly": node["active_users_monthly"],
                "signup": node["signup"],
                "local_posts": node["local_posts"],
                "user_post_ratio": node["total_users"] / local_posts,
            }
            bad_nodes.append(bad_node)
    print(json.dumps([bn["domain"] for bn in bad_nodes], indent=4))
else:
    # Print the error message if the request failed
    print(f'Request failed with status code {response.status_code}: {response.text}')
