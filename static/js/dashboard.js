/* =========================================================
   dashboard.js - Small dashboard utility helpers.
   Chart.js rendering itself lives inline in admin_dashboard.html
   (data is templated server-side), this file covers shared
   dashboard-only interactive touches such as animated counters.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    animateStatValues();
});

function animateStatValues() {
    const values = document.querySelectorAll('.stat-value');
    values.forEach(function (el) {
        const target = parseInt(el.textContent, 10);
        if (isNaN(target)) return;
        let current = 0;
        const step = Math.max(1, Math.ceil(target / 30));
        const interval = setInterval(function () {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(interval);
            }
            el.textContent = current;
        }, 20);
    });
}
