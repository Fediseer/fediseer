import os
import socket
from uuid import uuid4

from overseer.logger import logger
from overseer.flask import OVERSEER
from overseer.routes import * 
from overseer.apis import apiv1
from overseer.argparser import args
from overseer.consts import OVERSEER_VERSION


OVERSEER.register_blueprint(apiv1)


@OVERSEER.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, apikey, Client-Agent, X-Fields"
    response.headers["Horde-Node"] = f"{socket.gethostname()}:{args.port}:{OVERSEER_VERSION}"
    return response
