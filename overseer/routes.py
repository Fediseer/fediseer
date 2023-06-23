from flask import render_template, redirect, url_for, request
from markdown import markdown
from loguru import logger
from overseer.flask import OVERSEER
import overseer.exceptions as e

@logger.catch(reraise=True)
@OVERSEER.route('/')
# @cache.cached(timeout=300)
def index():
    with open(f'overseer/templates/index.md') as index_file:
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
    <title>Horde Overseer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {style}
    </head>
    """
    return(head + markdown(findex))

@logger.catch(reraise=True)
@OVERSEER.route('/.well-known/webfinger')
def wellknown_redirect():
    query_string = request.query_string.decode()
    if not query_string:
        return {"message":"No user specified"},400
    if query_string != "resource=acct:overseer@overseer.dbzer0.com":
        return {"message":"User does not exist"},404
    webfinger = {
        "subject": "acct:overseer@overseer.dbzer0.com",

        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": "https://overseer.dbzer0.com/actor"
            }
        ]
    }
    return webfinger,200