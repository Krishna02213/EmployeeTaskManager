"""
models/task.py
Task model represents work items assigned by admins to employees.
"""

from datetime import datetime, date
from models import db


class Task(db.Model):
    """Tasks table."""

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(10), nullable=False, default='Medium')  # Low / Medium / High
    status = db.Column(db.String(20), nullable=False, default='Pending')   # Pending / In Progress / Completed
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    due_date = db.Column(db.Date, nullable=True, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    comments = db.Column(db.Text, nullable=True, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("priority IN ('Low', 'Medium', 'High')", name='chk_task_priority'),
        db.CheckConstraint("status IN ('Pending', 'In Progress', 'Completed')", name='chk_task_status'),
        db.Index('idx_task_status', 'status'),
        db.Index('idx_task_priority', 'priority'),
        db.Index('idx_task_due_date', 'due_date'),
    )

    def is_overdue(self):
        """A task is overdue if its due date has passed and it's not completed."""
        if not self.due_date or self.status == 'Completed':
            return False
        return self.due_date < date.today()

    def add_comment(self, author_name, text):
        """Append a timestamped comment to the comments text field."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        entry = f"[{timestamp}] {author_name}: {text}"
        if self.comments:
            self.comments = self.comments + "\n" + entry
        else:
            self.comments = entry

    def comment_list(self):
        """Return comments split into a list for template rendering."""
        if not self.comments:
            return []
        return [line for line in self.comments.split('\n') if line.strip()]

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'assigned_by': self.assigned_by,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None,
            'is_overdue': self.is_overdue(),
        }

    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
