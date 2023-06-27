from dotenv import load_dotenv
import os
import logging

load_dotenv()

from fediseer.argparser import args
from fediseer.flask import OVERSEER
from loguru import logger
from fediseer.badges import generate_guarantee_badge
if __name__ == "__main__":
    # Only setting this for the WSGI logs
    print(generate_guarantee_badge("lemmy.dbzer0.com", "fediseer.com"))
