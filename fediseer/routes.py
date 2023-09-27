from flask import render_template, redirect, url_for, request
from markdown import markdown
from loguru import logger
from fediseer.flask import OVERSEER
from fediseer.faq import FEDISEER_FAQ
import fediseer.exceptions as e

@logger.catch(reraise=True)
@OVERSEER.route('/')
# @cache.cached(timeout=300)
def index():
    with open(f'fediseer/templates/index.md') as index_file:
        index = index_file.read()
    findex = index.format()

    style = """<style>
        body {
            max-width: 120ex;
            margin: 0 auto;
            color: #333333;
            line-height: 1.4;
            font-family: sans-serif;
            padding: 1em;
        }
        </style>
    """

    head = f"""<head>
    <title>Fediseer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {style}
    </head>
    """
    return(head + markdown(findex))

@logger.catch(reraise=True)
@OVERSEER.route('/faq')
# @cache.cached(timeout=300)
def faq():
    with open(f'fediseer/templates/faq.md') as md_file:
        md = md_file.read()

    style = """<style>
        body {
            max-width: 120ex;
            margin: 0 auto;
            color: #333333;
            line-height: 1.4;
            font-family: sans-serif;
            padding: 1em;
        }
        </style>
    """

    head = f"""<head>
    <title>Fediseer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {style}
    </head>
    """
    faq_dict = {}
    for entry in FEDISEER_FAQ:
        if entry["category"] not in faq_dict:
            faq_dict[entry["category"]] = []
        faq_dict[entry["category"]].append(entry)
    for category in faq_dict:
        md += f"#{category.capitalize()}\n\n"
        for entry in faq_dict[category]:
            md += f"## {entry['question']}\n\n{entry['document']}"
    return(head + markdown(md, extensions=['toc']
))

@logger.catch(reraise=True)
@OVERSEER.route('/.well-known/webfinger')
def wellknown_redirect():
    query_string = request.query_string.decode()
    if not query_string:
        return {"message":"No user specified"},400
    if query_string != "resource=acct:fediseer@fediseer.com":
        return {"message":"User does not exist"},404
    webfinger = {
        "subject": "acct:fediseer@fediseer.com",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": "https://fediseer.com/api/v1/user/fediseer"
            }
        ]
    }
    return webfinger,200

@logger.catch(reraise=True)
@OVERSEER.route('/inbox', methods=['POST'])
def inbox():
    # Access the JSON payload
    json_payload = request.get_json()
    actor = json_payload["actor"]
    message = json_payload["object"]["content"]
    logger.info(f"Shared Inbox Received: From: {actor} | {message}")
    return 'ok', 200
