from datetime import datetime
from sqlalchemy import Enum

from fediseer.flask import db, SQLITE_MODE
from fediseer import enums

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    # We don't do relations as we don't care if the columns are linked
    source_domain = db.Column(db.String(255), unique=False, nullable=False, index=True)
    target_domain = db.Column(db.String(255), unique=False, nullable=False, index=True)
    report_type = db.Column(Enum(enums.ReportType), nullable=False, index=True)
    report_activity = db.Column(Enum(enums.ReportActivity), nullable=False, index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)