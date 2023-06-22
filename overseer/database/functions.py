import time
import uuid
import json
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, not_, Boolean
from sqlalchemy.orm import noload
from overseer.flask import db, SQLITE_MODE
from overseer.utils import hash_api_key

from overseer.classes.instance import Instance

def get_all_instances():
    return db.session.query(Instance).all()


def find_instance_by_api_key(api_key):
    instance = Instance.query.filter_by(api_key=hash_api_key(api_key)).first()
    return instance

def find_instance_by_domain(domain):
    instance = Instance.query.filter_by(domain=domain).first()
    return instance

def find_authenticated_instance(domain,api_key):
    instance = Instance.query.filter_by(domain=domain, api_key=hash_api_key(api_key)).first()
    return instance