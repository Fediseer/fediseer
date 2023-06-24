import uuid
import os

import dateutil.relativedelta
from datetime import datetime
from sqlalchemy import Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from loguru import logger
from fediseer.flask import db, SQLITE_MODE

uuid_column_type = lambda: UUID(as_uuid=True) if not SQLITE_MODE else db.String(36)
   

class Claim(db.Model):
    __tablename__ = "claims"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = db.relationship("User", back_populates="claims")
    instance_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    instance = db.relationship("Instance", back_populates="admins")
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True) 
    account = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(255), unique=False, nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    claims = db.relationship("Claim", back_populates="user", cascade="all, delete-orphan")
