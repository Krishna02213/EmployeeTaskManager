"""
routes/admin.py
Admin blueprint: dashboard, employee management, task management,
search/filter, CSV export, and activity logs.
"""

import os
import re
import csv
import io
from datetime import datetime, date

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, current_app, Response, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from models import db
from models.user import User
from models.task import Task
from models.activity import ActivityLog
from routes.auth import role_required, EMAIL_REGEX

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

PHONE_REGEX = re.compile(r'^[0-9+\-\s]{7,20}$')


def allowed_file(filename):
    ext_ok = '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    return ext_ok


def save_profile_image(file_storage):
    """Safely save an uploaded profile image and return its stored filename."""
    if not file_storage or file_storage.filename == '':
        return None
    if not allowed_file(file_storage.filename):
        flash('Invalid image type. Allowed: png, jpg, jpeg, gif.', 'danger')
        return None
    filename = secure_filename(file_storage.filename)
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{filename}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file_storage.save(upload_path)
    return unique_name


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------
@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    total_employees = User.query.filter_by(role='employee').count()
    total_tasks = Task.query.count()
    pending_tasks = Task.query.filter_by(status='Pending').count()
    in_progress_tasks = Task.query.filter_by(status='In Progress').count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    overdue_tasks = Task.query.filter(
        Task.due_date < date.today(),
        Task.status != 'Completed'
    ).count()

    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    recent_employees = User.query.filter_by(role='employee').order_by(User.created_at.desc()).limit(5).all()

    # Department-wise employee counts for chart
    dept_rows = db.session.query(
        User.department, db.func.count(User.id)
    ).filter(User.role == 'employee').group_by(User.department).all()
    dept_labels = [row[0] or 'Unspecified' for row in dept_rows]
    dept_counts = [row[1] for row in dept_rows]

    task_dist = {
        'labels': ['Pending', 'In Progress', 'Completed'],
        'data': [pending_tasks, in_progress_tasks, completed_tasks],
    }

    return render_template(
        'admin_dashboard.html',
        total_employees=total_employees,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        recent_tasks=recent_tasks,
        recent_employees=recent_employees,
        dept_labels=dept_labels,
        dept_counts=dept_counts,
        task_dist=task_dist,
        today=date.today(),
    )


# ----------------------------------------------------------------------
# Employee Management
# ----------------------------------------------------------------------
@admin_bp.route('/employees')
@role_required('admin')
def employees():
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    sort = request.args.get('sort', 'latest')
    page = request.args.get('page', 1, type=int)

    query = User.query.filter_by(role='employee')

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                User.name.ilike(like),
                User.email.ilike(like),
                User.department.ilike(like),
            )
        )

    if department:
        query = query.filter(User.department == department)

    if sort == 'oldest':
        query = query.order_by(User.created_at.asc())
    elif sort == 'name':
        query = query.order_by(User.name.asc())
    else:
        query = query.order_by(User.created_at.desc())

    pagination = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False)
    departments = [row[0] for row in db.session.query(User.department).filter(
        User.role == 'employee', User.department.isnot(None)
    ).distinct().all()]

    return render_template(
        'employees.html',
        employees=pagination.items,
        pagination=pagination,
        search=search,
        department=department,
        sort=sort,
        departments=departments,
    )


@admin_bp.route('/employees/add', methods=['GET', 'POST'])
@role_required('admin')
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()
        joining_date_str = request.form.get('joining_date', '').strip()
        password = request.form.get('password', '')

        errors = []
        if not name:
            errors.append('Full name is required.')
        if not EMAIL_REGEX.match(email or ''):
            errors.append('A valid email is required.')
        if phone and not PHONE_REGEX.match(phone):
            errors.append('Please enter a valid phone number.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        joining_date = None
        if joining_date_str:
            try:
                joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid joining date format.')

        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('employee_form.html', employee=None, form_data=request.form)

        profile_image = save_profile_image(request.files.get('profile_image')) or 'default.png'

        employee = User(
            name=name,
            email=email,
            phone=phone,
            department=department,
            designation=designation,
            role='employee',
            profile_image=profile_image,
            joining_date=joining_date,
            status='active',
        )
        employee.set_password(password)
        db.session.add(employee)
        db.session.commit()

        ActivityLog.log(session['user_id'], f'Added employee: {employee.name} ({employee.email})')
        flash('Employee added successfully.', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('employee_form.html', employee=None, form_data=None)


@admin_bp.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_employee(employee_id):
    employee = User.query.filter_by(id=employee_id, role='employee').first_or_404()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        designation = request.form.get('designation', '').strip()
        joining_date_str = request.form.get('joining_date', '').strip()
        status = request.form.get('status', 'active')
        password = request.form.get('password', '')

        errors = []
        if not name:
            errors.append('Full name is required.')
        if not EMAIL_REGEX.match(email or ''):
            errors.append('A valid email is required.')
        if phone and not PHONE_REGEX.match(phone):
            errors.append('Please enter a valid phone number.')

        existing = User.query.filter(User.email == email, User.id != employee_id).first()
        if existing:
            errors.append('Another account already uses this email.')

        joining_date = employee.joining_date
        if joining_date_str:
            try:
                joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid joining date format.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('employee_form.html', employee=employee, form_data=request.form)

        employee.name = name
        employee.email = email
        employee.phone = phone
        employee.department = department
        employee.designation = designation
        employee.joining_date = joining_date
        employee.status = status

        if password:
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('employee_form.html', employee=employee, form_data=request.form)
            employee.set_password(password)

        new_image = save_profile_image(request.files.get('profile_image'))
        if new_image:
            employee.profile_image = new_image

        db.session.commit()
        ActivityLog.log(session['user_id'], f'Updated employee: {employee.name} ({employee.email})')
        flash('Employee updated successfully.', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('employee_form.html', employee=employee, form_data=None)


@admin_bp.route('/employees/delete/<int:employee_id>', methods=['POST'])
@role_required('admin')
def delete_employee(employee_id):
    employee = User.query.filter_by(id=employee_id, role='employee').first_or_404()
    name = employee.name
    db.session.delete(employee)
    db.session.commit()
    ActivityLog.log(session['user_id'], f'Deleted employee: {name}')
    flash('Employee deleted successfully.', 'success')
    return redirect(url_for('admin.employees'))


# ----------------------------------------------------------------------
# Task Management
# ----------------------------------------------------------------------
@admin_bp.route('/tasks')
@role_required('admin')
def tasks():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    due_filter = request.args.get('due', '').strip()
    sort = request.args.get('sort', 'latest')
    page = request.args.get('page', 1, type=int)

    query = Task.query

    if search:
        like = f"%{search}%"
        query = query.filter(Task.title.ilike(like))

    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    if due_filter == 'overdue':
        query = query.filter(Task.due_date < date.today(), Task.status != 'Completed')
    elif due_filter == 'today':
        query = query.filter(Task.due_date == date.today())
    elif due_filter == 'week':
        from datetime import timedelta
        query = query.filter(Task.due_date.between(date.today(), date.today() + timedelta(days=7)))

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
    employees_list = User.query.filter_by(role='employee', status='active').order_by(User.name).all()

    return render_template(
        'tasks.html',
        tasks=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
        priority=priority,
        due=due_filter,
        sort=sort,
        employees=employees_list,
        today=date.today(),
    )


@admin_bp.route('/tasks/add', methods=['GET', 'POST'])
@role_required('admin')
def add_task():
    employees_list = User.query.filter_by(role='employee', status='active').order_by(User.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium')
        assigned_to = request.form.get('assigned_to', type=int)
        due_date_str = request.form.get('due_date', '').strip()

        errors = []
        if not title:
            errors.append('Task title is required.')
        if priority not in ('Low', 'Medium', 'High'):
            errors.append('Invalid priority selected.')
        if not assigned_to or not User.query.filter_by(id=assigned_to, role='employee').first():
            errors.append('Please select a valid employee to assign this task to.')

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid due date format.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('task_form.html', task=None, employees=employees_list, form_data=request.form)

        task = Task(
            title=title,
            description=description,
            priority=priority,
            status='Pending',
            assigned_to=assigned_to,
            assigned_by=session['user_id'],
            due_date=due_date,
        )
        db.session.add(task)
        db.session.commit()

        ActivityLog.log(session['user_id'], f'Assigned task "{task.title}" to employee ID {assigned_to}')
        flash('Task assigned successfully.', 'success')
        return redirect(url_for('admin.tasks'))

    return render_template('task_form.html', task=None, employees=employees_list, form_data=None)


@admin_bp.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    employees_list = User.query.filter_by(role='employee', status='active').order_by(User.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium')
        status = request.form.get('status', task.status)
        assigned_to = request.form.get('assigned_to', type=int)
        due_date_str = request.form.get('due_date', '').strip()

        errors = []
        if not title:
            errors.append('Task title is required.')
        if priority not in ('Low', 'Medium', 'High'):
            errors.append('Invalid priority selected.')
        if status not in ('Pending', 'In Progress', 'Completed'):
            errors.append('Invalid status selected.')
        if not assigned_to or not User.query.filter_by(id=assigned_to, role='employee').first():
            errors.append('Please select a valid employee.')

        due_date = task.due_date
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid due date format.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('task_form.html', task=task, employees=employees_list, form_data=request.form)

        task.title = title
        task.description = description
        task.priority = priority
        task.assigned_to = assigned_to
        task.due_date = due_date

        if status != task.status:
            task.status = status
            if status == 'Completed':
                task.completed_at = datetime.utcnow()
            else:
                task.completed_at = None

        db.session.commit()
        ActivityLog.log(session['user_id'], f'Updated task "{task.title}" (ID {task.id})')
        flash('Task updated successfully.', 'success')
        return redirect(url_for('admin.tasks'))

    return render_template('task_form.html', task=task, employees=employees_list, form_data=None)


@admin_bp.route('/tasks/delete/<int:task_id>', methods=['POST'])
@role_required('admin')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    title = task.title
    db.session.delete(task)
    db.session.commit()
    ActivityLog.log(session['user_id'], f'Deleted task "{title}" (ID {task_id})')
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('admin.tasks'))


@admin_bp.route('/tasks/progress')
@role_required('admin')
def task_progress():
    """View task progress overview (pending / in progress / completed / overdue)."""
    view = request.args.get('view', 'all')
    query = Task.query

    if view == 'completed':
        query = query.filter_by(status='Completed')
    elif view == 'pending':
        query = query.filter_by(status='Pending')
    elif view == 'overdue':
        query = query.filter(Task.due_date < date.today(), Task.status != 'Completed')

    task_items = query.order_by(Task.due_date.asc()).all()
    return render_template('tasks.html', tasks=task_items, pagination=None, search='', status='',
                            priority='', due='', sort='latest',
                            employees=User.query.filter_by(role='employee').all(), today=date.today(),
                            progress_view=view)


# ----------------------------------------------------------------------
# CSV Export
# ----------------------------------------------------------------------
@admin_bp.route('/tasks/export')
@role_required('admin')
def export_tasks_csv():
    tasks_list = Task.query.order_by(Task.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Task ID', 'Title', 'Description', 'Priority', 'Status',
        'Assigned To', 'Assigned By', 'Due Date', 'Created Date',
        'Completed Date'
    ])

    for t in tasks_list:
        writer.writerow([
            t.id,
            t.title,
            t.description or '',
            t.priority,
            t.status,
            t.employee.name if t.employee else '',
            t.assigner.name if t.assigner else '',
            t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
            t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else '',
            t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else '',
        ])

    ActivityLog.log(session['user_id'], 'Exported tasks to CSV')

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=tasks_export.csv'
    return response


# ----------------------------------------------------------------------
# Activity Logs
# ----------------------------------------------------------------------
@admin_bp.route('/activity-logs')
@role_required('admin')
def activity_logs():
    page = request.args.get('page', 1, type=int)
    pagination = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE'], error_out=False
    )
    return render_template('activity_logs.html', logs=pagination.items, pagination=pagination)
