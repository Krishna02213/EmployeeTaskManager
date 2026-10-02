"""
models/user.py
User model represents both Admin and Employee accounts (differentiated by role).
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


def _get_db():
    from models import db
    return db


db = _get_db()


class User(db.Model):
    """User table stores admins and employees."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(100), nullable=True, index=True)
    designation = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # 'admin' or 'employee'
    profile_image = db.Column(db.String(255), nullable=True, default='default.png')
    joining_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assigned_tasks = db.relationship(
        'Task',
        foreign_keys='Task.assigned_to',
        backref='employee',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    created_tasks = db.relationship(
        'Task',
        foreign_keys='Task.assigned_by',
        backref='assigner',
        lazy='dynamic'
    )
    activity_logs = db.relationship(
        'ActivityLog',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'employee')", name='chk_user_role'),
        db.CheckConstraint("status IN ('active', 'inactive')", name='chk_user_status'),
        db.Index('idx_user_department', 'department'),
    )

    def set_password(self, raw_password):
        """Hash and store the given plaintext password."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    def is_admin(self):
        return self.role == 'admin'

    def is_active_user(self):
        return self.status == 'active'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'designation': self.designation,
            'role': self.role,
            'profile_image': self.profile_image,
            'joining_date': self.joining_date.strftime('%Y-%m-%d') if self.joining_date else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
