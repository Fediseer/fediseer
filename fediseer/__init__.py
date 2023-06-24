import os
import socket
from uuid import uuid4

from fediseer.logger import logger
from fediseer.flask import OVERSEER
from fediseer.routes import * 
from fediseer.apis import apiv1
from fediseer.argparser import args
from fediseer.consts import OVERSEER_VERSION


OVERSEER.register_blueprint(apiv1)


@OVERSEER.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, apikey, Client-Agent, X-Fields"
    response.headers["Horde-Node"] = f"{socket.gethostname()}:{args.port}:{OVERSEER_VERSION}"
    return response
