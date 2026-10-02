"""
models/activity.py
ActivityLog model records user actions for audit purposes.
"""

from datetime import datetime
from models import db


class ActivityLog(db.Model):
    """Activity logs table."""

    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index('idx_activity_timestamp', 'timestamp'),
    )

    @staticmethod
    def log(user_id, action):
        """Create and persist a new activity log entry."""
        entry = ActivityLog(user_id=user_id, action=action)
        db.session.add(entry)
        db.session.commit()
        return entry

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
        }

    def __repr__(self):
        return f'<ActivityLog {self.id}: {self.action}>'
