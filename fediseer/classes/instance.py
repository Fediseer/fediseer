import uuid
import os

import dateutil.relativedelta
from datetime import datetime
from sqlalchemy import Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from loguru import logger
from fediseer.flask import db, SQLITE_MODE

uuid_column_type = lambda: UUID(as_uuid=True) if not SQLITE_MODE else db.String(36)

# This is used to know when last time an instance removed their guarantee from another to prevent trolling/spamming
# By someone adding/removing guarantees
class RejectionRecord(db.Model):   
    __tablename__ = "rejection_records"
    __table_args__ = (UniqueConstraint('rejector_id', 'rejected_id', name='endoresements_rejector_id_rejected_id'),)
    id = db.Column(db.Integer, primary_key=True)
    rejector_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    rejector_instance = db.relationship("Instance", back_populates="rejections", foreign_keys=[rejector_id])
    rejected_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    rejected_instance = db.relationship("Instance", back_populates="rejectors", foreign_keys=[rejected_id])
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    performed = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def refresh(self):
        self.performed = datetime.utcnow()


class Guarantee(db.Model):
    __tablename__ = "guarantees"
    id = db.Column(db.Integer, primary_key=True)
    guarantor_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    guarantor_instance = db.relationship("Instance", back_populates="guarantees", foreign_keys=[guarantor_id])
    guaranteed_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), unique=True, nullable=False)
    guaranteed_instance = db.relationship("Instance", back_populates="guarantors", foreign_keys=[guaranteed_id])
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Endorsement(db.Model):
    __tablename__ = "endorsements"
    __table_args__ = (UniqueConstraint('approving_id', 'endorsed_id', name='endoresements_approving_id_endorsed_id'),)
    id = db.Column(db.Integer, primary_key=True)
    approving_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    approving_instance = db.relationship("Instance", back_populates="approvals", foreign_keys=[approving_id])
    endorsed_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    endorsed_instance = db.relationship("Instance", back_populates="endorsements", foreign_keys=[endorsed_id])
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Instance(db.Model):
    __tablename__ = "instances"

    id = db.Column(db.Integer, primary_key=True) 
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    oprhan_since = db.Column(db.DateTime, nullable=True)

    open_registrations = db.Column(db.Boolean, unique=False, nullable=False, index=True)
    email_verify = db.Column(db.Boolean, unique=False, nullable=False, index=True)
    software = db.Column(db.String(50), unique=False, nullable=False, index=True)

    approvals = db.relationship("Endorsement", back_populates="approving_instance", cascade="all, delete-orphan", foreign_keys=[Endorsement.approving_id])
    endorsements = db.relationship("Endorsement", back_populates="endorsed_instance", cascade="all, delete-orphan", foreign_keys=[Endorsement.endorsed_id])
    guarantees = db.relationship("Guarantee", back_populates="guarantor_instance", cascade="all, delete-orphan", foreign_keys=[Guarantee.guarantor_id])
    guarantors = db.relationship("Guarantee", back_populates="guaranteed_instance", cascade="all, delete-orphan", foreign_keys=[Guarantee.guaranteed_id])
    rejections = db.relationship("RejectionRecord", back_populates="rejector_instance", cascade="all, delete-orphan", foreign_keys=[RejectionRecord.rejector_id])
    rejectors = db.relationship("RejectionRecord", back_populates="rejected_instance", cascade="all, delete-orphan", foreign_keys=[RejectionRecord.rejected_id])
    admins = db.relationship("Claim", back_populates="instance", cascade="all, delete-orphan")

    def create(self):
        db.session.add(self)
        db.session.commit()

    def get_details(self):
        ret_dict = {
            "id": self.id,
            "domain": self.domain,
            "open_registrations": self.open_registrations,
            "email_verify": self.email_verify,
            "endorsements": len(self.endorsements),
            "approvals": len(self.approvals),
            "guarantor": self.get_guarantor_domain(),
        }
        return ret_dict


    def get_guarantee(self):
        if len(self.guarantors) == 0:
            return None
        return self.guarantors[0]

    def get_guarantor(self):
        guarantee = self.get_guarantee()
        if not guarantee:
            return None
        return guarantee.guarantor_instance
        return Instance.query.filter_by(id=guarantee.guarantor_id).first()

    def get_guarantor_domain(self):
        guarantor = self.get_guarantor()
        return guarantor.domain if guarantor else None

    def set_as_oprhan(self):
        self.oprhan_since = datetime.utcnow()
        db.session.commit()
    
    def unset_as_orphan(self):
        self.oprhan_since = None
        db.session.commit()
        