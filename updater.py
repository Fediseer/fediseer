from dotenv import load_dotenv
import os
import logging

load_dotenv()

from loguru import logger
from fediseer.flask import OVERSEER, db 
import fediseer.database.functions as database
from fediseer.register import ensure_instance_registered
from concurrent.futures import ThreadPoolExecutor

def refresh_info(domain):
    logger.info(f"Refreshing domain '{domain}")
    with OVERSEER.app_context():
        try:
            ensure_instance_registered(
                domain,
                # We  don't want to set allow_unreachable = True here
                # As InstanceInfo() won't raise an exception when failing
                # Which will cause the poll_failures not not increment
                allow_unreachable=False,
                record_unreachable=True,
                allowed_timeout=20
            )
        except Exception as err:
            pass

if __name__ == "__main__":
    # Only setting this for the WSGI logs
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s', level=logging.WARNING)

    logger.init("Updater", status="Starting")
    # try: # Debug
    #     with OVERSEER.app_context():
    #         ensure_instance_registered(
    #             "firefish.social",
    #             allow_unreachable=False,
    #             record_unreachable=True,
    #             allowed_timeout=20
    #         )         
    # except Exception as err:
    #     logger.error(err)
    futures = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        with OVERSEER.app_context():
            for instance in database.get_all_instances(0,0):
                if instance.software == 'wildcard':
                    continue
                futures.append(executor.submit(refresh_info, instance.domain))
                if len(futures) >= 500:
                    for future in futures:
                        future.result()
                    futures = []
            for future in futures:
                future.result()

    logger.init("Updater", status="Ended")
[]