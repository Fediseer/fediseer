from dotenv import load_dotenv
import os
import logging

load_dotenv()

from loguru import logger
from fediseer.flask import OVERSEER, db 
import fediseer.database.functions as database
from fediseer.register import ensure_instance_registered


if __name__ == "__main__":
    # Only setting this for the WSGI logs
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s', level=logging.WARNING)

    logger.init("Updater", status="Starting")
    with OVERSEER.app_context():
        for instance in database.get_all_instances(0,0):
            break
            logger.info(f"Refreshing domain '{instance.domain}")
            ensure_instance_registered(instance.domain)
    logger.init("Updater", status="Ended")
