"""
routes/employee.py
Employee blueprint: dashboard, task viewing/updating, profile, password change.
"""

import os
from datetime import datetime, date, timedelta

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, current_app
)

from models import db
from models.user import User
from models.task import Task
from models.activity import ActivityLog
from routes.auth import role_required, EMAIL_REGEX
from routes.admin import save_profile_image, PHONE_REGEX

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def current_user():
    return User.query.get(session['user_id'])


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------
@employee_bp.route('/dashboard')
@role_required('employee')
def dashboard():
    user = current_user()

    my_tasks = Task.query.filter_by(assigned_to=user.id)
    pending = my_tasks.filter_by(status='Pending').count()
    in_progress = my_tasks.filter_by(status='In Progress').count()
    completed = my_tasks.filter_by(status='Completed').count()

    upcoming_deadlines = Task.query.filter(
        Task.assigned_to == user.id,
        Task.status != 'Completed',
        Task.due_date.isnot(None),
        Task.due_date.between(date.today(), date.today() + timedelta(days=7))
    ).order_by(Task.due_date.asc()).limit(5).all()

    recent_activity = ActivityLog.query.filter_by(user_id=user.id).order_by(
        ActivityLog.timestamp.desc()
    ).limit(5).all()

    recent_tasks = Task.query.filter_by(assigned_to=user.id).order_by(
        Task.created_at.desc()
    ).limit(5).all()

    return render_template(
        'employee_dashboard.html',
        user=user,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        upcoming_deadlines=upcoming_deadlines,
        recent_activity=recent_activity,
        recent_tasks=recent_tasks,
        today=date.today(),
    )


# ----------------------------------------------------------------------
# Tasks
# ----------------------------------------------------------------------
@employee_bp.route('/tasks')
@role_required('employee')
def my_tasks():
    user = current_user()
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    sort = request.args.get('sort', 'latest')
    page = request.args.get('page', 1, type=int)

    query = Task.query.filter_by(assigned_to=user.id)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    if sort == 'oldest':
        query = query.order_by(Task.created_at.asc())
    elif sort == 'due_date':
        query = query.order_by(Task.due_date.asc())
    elif sort == 'priority':
        priority_order = db.case(
            (Task.priority == 'High', 1),
            (Task.priority == 'Medium', 2),
            (Task.priority == 'Low', 3),
            else_=4
        )
        query = query.order_by(priority_order)
    else:
        query = query.order_by(Task.created_at.desc())

    pagination = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False)

    return render_template(
        'tasks.html',
        tasks=pagination.items,
        pagination=pagination,
        search='',
        status=status,
        priority=priority,
        due='',
        sort=sort,
        employees=[],
        today=date.today(),
        employee_view=True,
    )


@employee_bp.route('/tasks/<int:task_id>/status', methods=['POST'])
@role_required('employee')
def update_task_status(task_id):
    user = current_user()
    task = Task.query.filter_by(id=task_id, assigned_to=user.id).first_or_404()

    new_status = request.form.get('status', '').strip()
    if new_status not in ('Pending', 'In Progress', 'Completed'):
        flash('Invalid status value.', 'danger')
        return redirect(url_for('employee.my_tasks'))

    task.status = new_status
    task.completed_at = datetime.utcnow() if new_status == 'Completed' else None
    db.session.commit()

    ActivityLog.log(user.id, f'Updated status of task "{task.title}" to {new_status}')
    flash('Task status updated.', 'success')
    return redirect(request.referrer or url_for('employee.my_tasks'))


@employee_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@role_required('employee')
def mark_completed(task_id):
    user = current_user()
    task = Task.query.filter_by(id=task_id, assigned_to=user.id).first_or_404()

    task.status = 'Completed'
    task.completed_at = datetime.utcnow()
    db.session.commit()

    ActivityLog.log(user.id, f'Marked task "{task.title}" as completed')
    flash('Task marked as completed!', 'success')
    return redirect(request.referrer or url_for('employee.my_tasks'))


@employee_bp.route('/tasks/<int:task_id>/comment', methods=['POST'])
@role_required('employee')
def add_comment(task_id):
    user = current_user()
    task = Task.query.filter_by(id=task_id, assigned_to=user.id).first_or_404()

    text = request.form.get('comment', '').strip()
    if not text:
        flash('Comment cannot be empty.', 'danger')
        return redirect(request.referrer or url_for('employee.my_tasks'))

    task.add_comment(user.name, text)
    db.session.commit()

    ActivityLog.log(user.id, f'Commented on task "{task.title}"')
    flash('Comment added.', 'success')
    return redirect(request.referrer or url_for('employee.my_tasks'))


# ----------------------------------------------------------------------
# Profile
# ----------------------------------------------------------------------
@employee_bp.route('/profile')
@role_required('employee')
def profile():
    user = current_user()
    return render_template('profile.html', user=user)


@employee_bp.route('/profile/edit', methods=['GET', 'POST'])
@role_required('employee')
def edit_profile():
    user = current_user()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()

        errors = []
        if not name:
            errors.append('Full name is required.')
        if phone and not PHONE_REGEX.match(phone):
            errors.append('Please enter a valid phone number.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('profile.html', user=user, editing=True)

        user.name = name
        user.phone = phone
        user.department = department
        user.designation = designation

        new_image = save_profile_image(request.files.get('profile_image'))
        if new_image:
            user.profile_image = new_image
            session['profile_image'] = new_image

        session['name'] = name
        db.session.commit()

        ActivityLog.log(user.id, 'Updated profile information')
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('employee.profile'))

    return render_template('profile.html', user=user, editing=True)


@employee_bp.route('/change-password', methods=['GET', 'POST'])
@role_required('employee')
def change_password():
    user = current_user()

    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not user.check_password(current_pw):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')

        if len(new_pw) < 6:
            flash('New password must be at least 6 characters.', 'danger')
            return render_template('change_password.html')

        if new_pw != confirm_pw:
            flash('New password and confirmation do not match.', 'danger')
            return render_template('change_password.html')

        user.set_password(new_pw)
        db.session.commit()

        ActivityLog.log(user.id, 'Changed account password')
        flash('Password changed successfully.', 'success')
        return redirect(url_for('employee.profile'))

    return render_template('change_password.html')
