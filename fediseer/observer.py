import requests
from loguru import logger
from fediseer.consts import FEDISEER_VERSION

def retrieve_suspicious_instances(activity_suspicion = 20, active_suspicious = 500, activity_suspicion_low = 400):
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
        comment_counts
    }
    }
    '''

    # GraphQL endpoint URL
    url = 'https://api.fediverse.observer/'

    # Request headers
    headers = {
        'User-Agent': f'Fediseer/{FEDISEER_VERSION}',
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
            local_activity = node["local_posts"] + node["comment_counts"]
            if node["total_users"] < 300:
                continue
            if local_activity == 0:
                local_activity= 1

            # posts+comments could be much lower than total users
            if node["total_users"] / local_activity > activity_suspicion:
                is_bad = True
                # print(node)

            # posts+comments could be much higher than total users
            if local_activity / node["total_users"] > activity_suspicion_low:
                is_bad = True
                # print(node)

            # check active users (monthly is a lot lower than total users)
            local_active_monthly_users = node["active_users_monthly"]
            # Avoid division by 0
            if local_active_monthly_users == 0:
                local_active_monthly_users= 0.5
            if node["total_users"] / local_active_monthly_users > active_suspicious:
                is_bad = True
                # print(node)

            if is_bad:
                bad_node = {
                    "domain": node["domain"],
                    "uptime_alltime": node["uptime_alltime"],
                    "local_posts": node["local_posts"],
                    "comment_counts": node["comment_counts"],
                    "total_users": node["total_users"],
                    "active_users_monthly": node["active_users_monthly"],
                    "signup": node["signup"],
                    "activity_suspicion": node["total_users"] / local_activity,
                    "active_users_suspicion": node["total_users"] / local_active_monthly_users,
                }
                bad_nodes.append(bad_node)
        return bad_nodes
    else:
        # Print the error message if the request failed
        logger.error(f'Observer failed with status code {response.status_code}: {response.text}')
        return None
