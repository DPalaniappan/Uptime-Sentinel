from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from app.extensions import db
from enum import Enum



user_targets = db.Table('user_targets',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('target_id', db.Integer, db.ForeignKey('target.id'), primary_key=True)
)

class TargetStatus(str, Enum):
    ACTIVE = 'active'
    QUARANTINED = 'quarantined'
    INACTIVE = 'inactive'   


class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_ping = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(TargetStatus), default=TargetStatus.ACTIVE, nullable=False)
    consecutive_failures = db.Column(db.Integer, default=0)
    status_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    currently_online = db.relationship('PingLog', backref='current_status', lazy=True, uselist=False, primaryjoin="and_(Target.id==PingLog.target_id, PingLog.timestamp==Target.last_ping)")
    pings = db.relationship('PingLog', backref='target', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'created_at': self.created_at.isoformat(),
            'consecutive_failures': self.consecutive_failures
        }
    
    def display_target_info(self):
        return {
            'url': self.url,
            'added_on': self.created_at.isoformat(),
            'last_ping': self.last_ping.isoformat() if self.last_ping else None,
            'status': self.status.value,
            'status_changed_at': self.status_changed_at.isoformat(),
            'currently_online': self.currently_online
        }
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    targets = db.relationship('Target', secondary=user_targets, backref=db.backref('users', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email
        }



class PingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float, nullable=False)
    is_online = db.Column(db.Boolean, nullable=False)
    status_code = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'target_id': self.target_id,
            'timestamp': self.timestamp.isoformat(),
            'response_time': self.response_time,
            'is_online': self.is_online,
            'status_code': self.status_code
        }

