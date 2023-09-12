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

class Censure(db.Model):
    __tablename__ = "censures"
    __table_args__ = (UniqueConstraint('censuring_id', 'censured_id', name='censures_censuring_id_censured_id'),)
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255), unique=False, nullable=True, index=False)
    evidence = db.Column(db.Text, unique=False, nullable=True, index=False)
    censuring_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    censuring_instance = db.relationship("Instance", back_populates="censures_given", foreign_keys=[censuring_id])
    censured_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    censured_instance = db.relationship("Instance", back_populates="censures_received", foreign_keys=[censured_id])
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Hesitation(db.Model):
    __tablename__ = "hesitations"
    __table_args__ = (UniqueConstraint('hesitant_id', 'dubious_id', name='hesitations_hesitant_id_dubious_id'),)
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255), unique=False, nullable=True, index=False)
    evidence = db.Column(db.Text, unique=False, nullable=True, index=False)
    hesitant_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    hesitating_instance = db.relationship("Instance", back_populates="hesitations_given", foreign_keys=[hesitant_id])
    dubious_id = db.Column(db.Integer, db.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False)
    dubious_instance = db.relationship("Instance", back_populates="hesitations_received", foreign_keys=[dubious_id])
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
    sysadmins = db.Column(db.Integer, unique=False, nullable=True)
    moderators = db.Column(db.Integer, unique=False, nullable=True)

    approvals = db.relationship("Endorsement", back_populates="approving_instance", cascade="all, delete-orphan", foreign_keys=[Endorsement.approving_id])
    endorsements = db.relationship("Endorsement", back_populates="endorsed_instance", cascade="all, delete-orphan", foreign_keys=[Endorsement.endorsed_id])
    censures_given = db.relationship("Censure", back_populates="censuring_instance", cascade="all, delete-orphan", foreign_keys=[Censure.censuring_id])
    censures_received = db.relationship("Censure", back_populates="censured_instance", cascade="all, delete-orphan", foreign_keys=[Censure.censured_id])
    hesitations_given = db.relationship("Hesitation", back_populates="hesitating_instance", cascade="all, delete-orphan", foreign_keys=[Hesitation.hesitant_id])
    hesitations_received = db.relationship("Hesitation", back_populates="dubious_instance", cascade="all, delete-orphan", foreign_keys=[Hesitation.dubious_id])
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
            "software": self.software,
            "claimed": len(self.admins),
            "open_registrations": self.open_registrations,
            "email_verify": self.email_verify,
            "endorsements": len(self.endorsements),
            "approvals": len(self.approvals),
            "guarantor": self.get_guarantor_domain(),
            "sysadmins": self.sysadmins,
            "moderators": self.moderators,
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
