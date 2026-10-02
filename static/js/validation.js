/* =========================================================
   validation.js - Client-side form validation helpers
   Applies to Employee and Task forms across the app.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    validateEmployeeForm();
    validateTaskForm();
});

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_PATTERN = /^[0-9+\-\s]{7,20}$/;

function showFieldError(input, message) {
    clearFieldError(input);
    const error = document.createElement('span');
    error.className = 'error-text field-error';
    error.textContent = message;
    input.insertAdjacentElement('afterend', error);
    input.style.borderColor = 'var(--danger)';
}

function clearFieldError(input) {
    input.style.borderColor = '';
    const next = input.nextElementSibling;
    if (next && next.classList.contains('field-error')) {
        next.remove();
    }
}

function validateEmployeeForm() {
    const form = document.getElementById('employeeForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        let valid = true;

        const name = document.getElementById('name');
        const email = document.getElementById('email');
        const phone = document.getElementById('phone');
        const password = document.getElementById('password');
        const joiningDate = document.getElementById('joining_date');

        [name, email, phone, password, joiningDate].forEach(function (el) {
            if (el) clearFieldError(el);
        });

        if (name && !name.value.trim()) {
            showFieldError(name, 'Full name is required.');
            valid = false;
        }

        if (email && !EMAIL_PATTERN.test(email.value.trim())) {
            showFieldError(email, 'Please enter a valid email address.');
            valid = false;
        }

        if (phone && phone.value.trim() && !PHONE_PATTERN.test(phone.value.trim())) {
            showFieldError(phone, 'Please enter a valid phone number.');
            valid = false;
        }

        if (password && password.hasAttribute('required') && password.value.length < 6) {
            showFieldError(password, 'Password must be at least 6 characters.');
            valid = false;
        }

        if (joiningDate && joiningDate.value) {
            const selected = new Date(joiningDate.value);
            const today = new Date();
            if (selected > today) {
                showFieldError(joiningDate, 'Joining date cannot be in the future.');
                valid = false;
            }
        }

        if (!valid) e.preventDefault();
    });
}

function validateTaskForm() {
    const form = document.getElementById('taskForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        let valid = true;

        const title = document.getElementById('title');
        const assignedTo = document.getElementById('assigned_to');
        const dueDate = document.getElementById('due_date');

        [title, assignedTo, dueDate].forEach(function (el) {
            if (el) clearFieldError(el);
        });

        if (title && !title.value.trim()) {
            showFieldError(title, 'Task title is required.');
            valid = false;
        }

        if (assignedTo && !assignedTo.value) {
            showFieldError(assignedTo, 'Please select an employee.');
            valid = false;
        }

        if (dueDate && dueDate.value) {
            const selected = new Date(dueDate.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            if (selected < today) {
                showFieldError(dueDate, 'Due date cannot be in the past.');
                valid = false;
            }
        }

        if (!valid) e.preventDefault();
    });
}
