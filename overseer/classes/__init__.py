import os
from loguru import logger
from overseer.argparser import args
from importlib import import_module
from overseer.flask import db, OVERSEER
from overseer.utils import hash_api_key

# Importing for DB creation
from overseer.classes.instance import Instance, Guarantee

with OVERSEER.app_context():

    db.create_all()

    admin_domain = os.getenv("ADMIN_DOMAIN")
    admin = db.session.query(Instance).filter_by(domain=admin_domain).first()
    if not admin:
        admin = Instance(
            id=0,
            domain=admin_domain,
            api_key=hash_api_key(os.getenv("ADMIN_PASSWORD")),
            open_registrations=False,
            email_verify=False,
        )
        admin.create()
        guarantee = Guarantee(
            guarantor_id = admin.id,
            guaranteed_id = admin.id,
        )
        db.session.add(guarantee)
        db.session.commit()