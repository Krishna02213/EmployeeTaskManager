"""
models package
Initializes the shared SQLAlchemy database instance used across the app.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they are registered with SQLAlchemy metadata
from models.user import User          # noqa: E402,F401
from models.task import Task          # noqa: E402,F401
from models.activity import ActivityLog  # noqa: E402,F401
