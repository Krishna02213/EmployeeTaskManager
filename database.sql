-- =====================================================================
-- database.sql
-- Employee Task Management System - MySQL Database Schema
-- =====================================================================
-- Note: The Flask app will auto-create these tables via SQLAlchemy on
-- first run (db.create_all()). This script is provided so the database
-- and schema can also be set up manually / independently if desired.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS employee_task_manager
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE employee_task_manager;

-- ---------------------------------------------------------------------
-- Table: users
-- Stores both Admin and Employee accounts.
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(120)  NOT NULL,
    email           VARCHAR(150)  NOT NULL UNIQUE,
    phone           VARCHAR(20)   DEFAULT NULL,
    department      VARCHAR(100)  DEFAULT NULL,
    designation     VARCHAR(100)  DEFAULT NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    role            VARCHAR(20)   NOT NULL DEFAULT 'employee',
    profile_image   VARCHAR(255)  DEFAULT 'default.png',
    joining_date    DATE          DEFAULT NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'active',
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_user_role CHECK (role IN ('admin', 'employee')),
    CONSTRAINT chk_user_status CHECK (status IN ('active', 'inactive')),

    INDEX idx_user_email (email),
    INDEX idx_user_department (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Table: tasks
-- Stores tasks assigned by admins to employees.
-- ---------------------------------------------------------------------
CREATE TABLE tasks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200)  NOT NULL,
    description     TEXT          DEFAULT NULL,
    priority        VARCHAR(10)   NOT NULL DEFAULT 'Medium',
    status          VARCHAR(20)   NOT NULL DEFAULT 'Pending',
    assigned_to     INT           NOT NULL,
    assigned_by     INT           DEFAULT NULL,
    due_date        DATE          DEFAULT NULL,
    completed_at    DATETIME      DEFAULT NULL,
    comments        TEXT          DEFAULT NULL,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_task_priority CHECK (priority IN ('Low', 'Medium', 'High')),
    CONSTRAINT chk_task_status CHECK (status IN ('Pending', 'In Progress', 'Completed')),

    CONSTRAINT fk_task_assigned_to
        FOREIGN KEY (assigned_to) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_task_assigned_by
        FOREIGN KEY (assigned_by) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_task_status (status),
    INDEX idx_task_priority (priority),
    INDEX idx_task_due_date (due_date),
    INDEX idx_task_assigned_to (assigned_to)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Table: activity_logs
-- Records auditable user actions.
-- ---------------------------------------------------------------------
CREATE TABLE activity_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    action      VARCHAR(255) NOT NULL,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_activity_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_activity_timestamp (timestamp),
    INDEX idx_activity_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Seed default administrator account
-- Email:    admin@example.com
-- Password: Admin@123
-- (Password hash below is a Werkzeug pbkdf2:sha256 hash of "Admin@123")
-- ---------------------------------------------------------------------
INSERT INTO users (name, email, phone, department, designation, password_hash, role, profile_image, status)
VALUES (
    'System Administrator',
    'admin@example.com',
    '0000000000',
    'Administration',
    'Administrator',
    'pbkdf2:sha256:600000$placeholderSaltValue$0000000000000000000000000000000000000000000000000000000000000',
    'admin',
    'default.png',
    'active'
);

-- NOTE: The placeholder hash above will NOT work for manual SQL-only setups.
-- The Flask application automatically seeds a working default admin account
-- with a correctly generated password hash the first time it runs
-- (see app.py -> seed_default_admin). If you set up the database using
-- ONLY this script (without running the Flask app), delete the row above
-- and let the application seed it on first launch instead.
