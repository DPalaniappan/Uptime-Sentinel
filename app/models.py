from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from app.extensions import db
from sqlalchemy import event
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_ping = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(TargetStatus), default=TargetStatus.ACTIVE, nullable=False)
    consecutive_failures = db.Column(db.Integer, default=0)
    status_changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_online = db.Column(db.Boolean, default=True)
    pings = db.relationship('PingLog', backref='target', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'consecutive_failures': self.consecutive_failures,
            'is_online': self.is_online
        }
    
    def display_target_info(self):
        return {
            'url': self.url,
            'added_on': self.created_at.strftime('%b %d, %Y %I:%M %p'),
            'last_ping': self.last_ping.strftime('%b %d, %Y %I:%M:%S %p') if self.last_ping else "Never",
            'status': self.status.value,
            'status_changed_at': self.status_changed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_online': self.is_online
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
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    response_time = db.Column(db.Float, nullable=True)
    is_online = db.Column(db.Boolean, nullable=False)
    status_code = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'target_id': self.target_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'response_time': f"{self.response_time:.3f}s" if self.response_time else "N/A",
            'is_online': self.is_online,
            'status_code': self.status_code
        }
