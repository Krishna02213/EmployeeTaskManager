# Employee Task Management Web Application

A complete, production-quality Employee Task Management system built with
**Flask + SQLAlchemy + MySQL** on the backend and **HTML5 / CSS3 / Vanilla
JavaScript** on the frontend (no React/Vue/Angular/Bootstrap/Tailwind).

---

## ✨ Features

**Admin**
- Login / Logout, Dashboard with stat cards and Chart.js charts
- Add / Edit / Delete / View / Search Employees
- Assign / Edit / Delete Tasks, view Task Progress (Pending / Completed / Overdue)
- Filter & sort tasks, Export tasks to CSV
- View system-wide Activity Logs

**Employee**
- Login / Logout, personal Dashboard
- View assigned tasks, update task status, mark tasks completed
- Add comments to tasks
- View/edit profile, upload profile picture, change password

**UI**
- Responsive sidebar + navbar, cards, data tables, search bars, filters,
  pagination, modals, toast notifications, confirmation dialogs, loading
  spinner, profile dropdown, dark mode toggle, mobile responsive layout.

**Security**
- Password hashing (Werkzeug), Flask session-based auth, role-based
  authorization decorators, CSRF protection (Flask-WTF), secure filename
  handling for uploads, parameterized ORM queries (SQL injection safe),
  input sanitization / validation on both client and server.

---

## 🗂️ Project Structure

```
EmployeeTaskManager/
├── app.py                  # Application factory & entry point
├── config.py                # Configuration (env-driven)
├── requirements.txt
├── database.sql             # Manual MySQL schema (optional; app auto-creates tables)
├── README.md
├── instance/
├── uploads/                 # Uploaded profile pictures
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── task.py
│   └── activity.py
├── routes/
│   ├── auth.py
│   ├── admin.py
│   └── employee.py
├── templates/
│   ├── base.html, login.html, admin_dashboard.html, employee_dashboard.html,
│   │   employees.html, employee_form.html, tasks.html, task_form.html,
│   │   profile.html, change_password.html, activity_logs.html, error.html
└── static/
    ├── css/ (style.css, dashboard.css, login.css)
    ├── js/ (script.js, validation.js, dashboard.js)
    └── images/ (default.png)
```

---

## ⚙️ Requirements

- Python 3.9+
- MySQL Server 8.x (or MariaDB 10.4+)
- pip

---

## 🚀 Installation Steps

### 1. Extract / clone the project and enter the folder
```bash
cd EmployeeTaskManager
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🐬 MySQL Setup Instructions

### Option A — Let the app create the schema automatically (recommended)
1. Create an empty database in MySQL:
   ```sql
   CREATE DATABASE employee_task_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Configure your `.env` (see below) with the correct credentials.
3. Run the app — `db.create_all()` in `app.py` will create all tables and
   seed the default admin account automatically on first launch.

### Option B — Use the provided `database.sql`
```bash
mysql -u root -p < database.sql
```
This creates the database, all three tables (`users`, `tasks`,
`activity_logs`) with primary keys, foreign keys, constraints and indexes.

> ⚠️ The seed admin row inside `database.sql` uses a placeholder password
> hash and will **not** let you log in. If you use Option B, delete that
> `INSERT` row (or just truncate the `users` table) and start the Flask
> app once — it will automatically seed a working default admin account
> with a correctly generated password hash.

---

## 🔐 Environment Configuration

Create a `.env` file in the project root (same folder as `app.py`):

```env
SECRET_KEY=replace-with-a-long-random-string
FLASK_ENV=development

DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=employee_task_manager

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=Admin@123
```

All values have sensible defaults in `config.py`, but you should always
override `SECRET_KEY` and your MySQL credentials.

---

## ▶️ Running the Application

```bash
# 1. Install dependencies (if not already done)
pip install -r requirements.txt

# 2. Make sure MySQL is running and the database exists (see MySQL Setup above)

# 3. Run the Flask development server
python app.py
```

The app will be available at **http://localhost:5000**

On first run, the app automatically:
- Creates all required tables (`users`, `tasks`, `activity_logs`)
- Seeds a default administrator account

---

## 🔑 Default Login Credentials

**Admin**
```
Email:    admin@example.com
Password: Admin@123
```

Create employee accounts from the Admin → Employees → "Add Employee" page;
each new employee can then log in with the email/password you set for them.

---

## 🧪 Quick Manual Test Checklist

1. Log in as admin using the credentials above.
2. Add a new employee (with a profile picture).
3. Assign a task to that employee with a due date and priority.
4. Log out, log back in as the employee (their email + the password you set).
5. Update the task status, mark it completed, add a comment.
6. Log back in as admin — verify the dashboard cards, charts, and activity
   logs reflect the changes; try CSV export and the search/filter bars.

---

## 🛠️ Tech Stack Summary

| Layer          | Technology                          |
|----------------|--------------------------------------|
| Backend        | Python 3, Flask, Flask-SQLAlchemy    |
| Database       | MySQL (via PyMySQL driver)           |
| Auth           | Flask Sessions + Werkzeug hashing    |
| Frontend       | HTML5, CSS3, Vanilla JavaScript      |
| Charts         | Chart.js (CDN)                       |
| CSRF           | Flask-WTF                            |

---

## 📄 License

This project was generated as a demonstration full-stack application and
is free to use and modify for learning or as a starting point for your
own projects.
