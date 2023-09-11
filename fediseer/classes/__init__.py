import os
from loguru import logger
from fediseer.argparser import args
from importlib import import_module
from fediseer.flask import db, OVERSEER
from fediseer.utils import hash_api_key

# Importing for DB creation
from fediseer.classes.instance import Instance, Guarantee
from fediseer.classes.user import User, Claim
import fediseer.classes.user
import fediseer.classes.reports

with OVERSEER.app_context():

    db.create_all()

    admin_domain = os.getenv("FEDISEER_LEMMY_DOMAIN")
    admin_instance = db.session.query(Instance).filter_by(domain=admin_domain).first()
    if not admin_instance:
        admin_instance = Instance(
            id=0,
            domain=admin_domain,
            open_registrations=False,
            email_verify=False,
            software="fediseer",
        )
        admin_instance.create()
        guarantee = Guarantee(
            id=0,
            guarantor_id = admin_instance.id,
            guaranteed_id = admin_instance.id,
        )
        db.session.add(guarantee)        
        db.session.commit()
        admin_user = User(
            id=0,
            account = "@fediseer@fediseer.com",
            username = "fediseer",
            api_key=hash_api_key(os.getenv("ADMIN_API_KEY")),
        )
        db.session.add(admin_user)
        db.session.commit()
        claim = Claim(
            id=0,
            user_id = admin_user.id,
            instance_id = admin_instance.id
        )
        db.session.add(claim)
        db.session.commit()