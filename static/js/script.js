/* =========================================================
   script.js - Global UI behavior: sidebar, dark mode,
   toasts, modals, confirmation dialogs, loading spinner.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    initSidebar();
    initDarkMode();
    initProfileDropdown();
    initFlashToasts();
    initLoadingSpinner();
});

/* ---------------- Sidebar (mobile) ---------------- */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    const openBtn = document.getElementById('sidebarToggle');
    const closeBtn = document.getElementById('sidebarClose');

    function openSidebar() {
        sidebar && sidebar.classList.add('open');
        backdrop && backdrop.classList.add('open');
    }
    function closeSidebar() {
        sidebar && sidebar.classList.remove('open');
        backdrop && backdrop.classList.remove('open');
    }

    openBtn && openBtn.addEventListener('click', openSidebar);
    closeBtn && closeBtn.addEventListener('click', closeSidebar);
    backdrop && backdrop.addEventListener('click', closeSidebar);
}

/* ---------------- Dark mode ---------------- */
function initDarkMode() {
    const toggle = document.getElementById('darkModeToggle');
    const html = document.documentElement;
    const saved = getCookie('theme');

    if (saved) {
        html.setAttribute('data-theme', saved);
        if (toggle) toggle.textContent = saved === 'dark' ? '☀️' : '🌙';
    }

    toggle && toggle.addEventListener('click', function () {
        const current = html.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', next);
        toggle.textContent = next === 'dark' ? '☀️' : '🌙';
        setCookie('theme', next, 365);
    });
}

function setCookie(name, value, days) {
    const d = new Date();
    d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = `${name}=${value};expires=${d.toUTCString()};path=/`;
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
}

/* ---------------- Profile dropdown ---------------- */
function initProfileDropdown() {
    const btn = document.getElementById('profileBtn');
    const menu = document.getElementById('profileMenu');
    if (!btn || !menu) return;

    btn.addEventListener('click', function (e) {
        e.stopPropagation();
        menu.classList.toggle('open');
    });

    document.addEventListener('click', function () {
        menu.classList.remove('open');
    });
}

/* ---------------- Toast notifications ---------------- */
function initFlashToasts() {
    const flashes = document.querySelectorAll('[data-autotoast]');
    flashes.forEach(function (el) {
        const category = el.getAttribute('data-autotoast');
        const message = el.getAttribute('data-msg');
        showToast(message, category);
    });
}

function showToast(message, category) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    const cls = ['success', 'danger', 'warning', 'info'].includes(category) ? category : 'info';
    toast.className = `toast toast-${cls}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
}

/* ---------------- Confirmation modal ---------------- */
function confirmDelete(actionUrl, message) {
    const modal = document.getElementById('confirmModal');
    const msgEl = document.getElementById('confirmMessage');
    const form = document.getElementById('confirmForm');
    if (!modal || !form) return;
    msgEl.textContent = message || 'Are you sure you want to proceed?';
    form.action = actionUrl;
    modal.classList.remove('hidden');
}

function closeConfirmModal() {
    const modal = document.getElementById('confirmModal');
    modal && modal.classList.add('hidden');
}

/* ---------------- Loading spinner on navigation ---------------- */
function initLoadingSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (!spinner) return;

    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            spinner.classList.remove('hidden');
        });
    });

    document.querySelectorAll('a.btn, .sidebar-nav a').forEach(function (link) {
        link.addEventListener('click', function () {
            spinner.classList.remove('hidden');
        });
    });

    window.addEventListener('pageshow', function () {
        spinner.classList.add('hidden');
    });
}
