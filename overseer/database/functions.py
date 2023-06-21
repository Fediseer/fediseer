import time
import uuid
import json
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, not_, Boolean
from sqlalchemy.orm import noload
from overseer.flask import db, SQLITE_MODE

from overseer.classes.instance import Instance

def get_all_instances():
    return db.session.query(Instance).all()
