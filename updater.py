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
        # try: # Debug
        #     ensure_instance_registered(
        #         "jorts.horse",
        #         allow_unreachable=False,
        #         record_unreachable=True,
        #         allowed_timeout=3
        #     )         
        # except:
        #     logger.error("failed")
        for instance in database.get_all_instances(0,0):
            if instance.software == 'wildcard':
                continue
            logger.info(f"Refreshing domain '{instance.domain}")
            try:
                ensure_instance_registered(
                    instance.domain,
                    # We  don't want to set allow_unreachable = True here
                    # As InstanceInfo() won't raise an exception when failing
                    # Which will cause the poll_failures not not increment
                    allow_unreachable=False,
                    record_unreachable=True,
                    allowed_timeout=20
                )
            except:
                logger.info(f"Recorded {instance.domain} as unreachable.")
    logger.init("Updater", status="Ended")
