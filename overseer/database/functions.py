import time
import uuid
import json
from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, not_, Boolean
from sqlalchemy.orm import noload
from overseer.flask import db, SQLITE_MODE
from overseer.utils import hash_api_key
from sqlalchemy.orm import joinedload
from overseer.classes.instance import Instance, Endorsement

def get_all_instances(min_endorsements = 0, min_guarantors = 1):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.endorsements,
        Instance.guarantors,
    ).options(
        joinedload(Instance.guarantors),
        joinedload(Instance.endorsements),
    ).group_by(
        Instance.id
    ).having(
        db.func.count(Instance.endorsements) >= min_endorsements,
    ).having(
        db.func.count(Instance.guarantors) >= min_guarantors,
    )
    return query.all()


def get_all_endorsed_instances_by_approving_id(approving_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.endorsements,
    ).options(
        joinedload(Instance.endorsements),
    ).filter(
        Endorsement.approving_id == approving_id
    ).group_by(
        Instance.id
    )
    return query.all()

def get_all_approving_instances_by_endorsed_id(endorsed_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.approvals,
    ).options(
        joinedload(Instance.approvals),
    ).filter(
        Endorsement.endorsed_id == endorsed_id
    ).group_by(
        Instance.id
    )
    return query.all()


def find_instance_by_api_key(api_key):
    instance = Instance.query.filter_by(api_key=hash_api_key(api_key)).first()
    return instance

def find_instance_by_domain(domain):
    instance = Instance.query.filter_by(domain=domain).first()
    return instance

def find_authenticated_instance(domain,api_key):
    instance = Instance.query.filter_by(domain=domain, api_key=hash_api_key(api_key)).first()
    return instance

def get_endorsement(instance_id, endorsing_instance_id):
    query = Endorsement.query.filter_by(
        endorsed_id=instance_id,
        approving_id=endorsing_instance_id,
    )
    return query.first()