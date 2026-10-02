"""
routes/auth.py
Handles login, logout, and authentication/authorization decorators.
"""

import re
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash, current_app
)

from models import db
from models.user import User
from models.activity import ActivityLog

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


# ----------------------------------------------------------------------
# Decorators
# ----------------------------------------------------------------------
def login_required(f):
    """Ensure a user is logged in before accessing a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    """Ensure the logged-in user has the given role (admin / employee)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') != role:
                flash('You are not authorized to access that page.', 'danger')
                if session.get('role') == 'admin':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('employee.dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@auth_bp.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('employee.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('employee.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Backend validation
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        if not EMAIL_REGEX.match(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html')

        # Parameterized ORM query prevents SQL injection
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        if not user.is_active_user():
            flash('Your account has been deactivated. Contact the administrator.', 'danger')
            return render_template('login.html')

        session.clear()
        session.permanent = True
        session['user_id'] = user.id
        session['role'] = user.role
        session['name'] = user.name
        session['profile_image'] = user.profile_image

        ActivityLog.log(user.id, f'{user.name} logged in')

        flash(f'Welcome back, {user.name}!', 'success')
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('employee.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        ActivityLog.log(session['user_id'], f"{session.get('name', 'User')} logged out")
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
