/* NyayaFlow - Shared JavaScript */

function updateNav() {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    const loginLink = document.getElementById('navLogin');
    const logoutLink = document.getElementById('navLogout');
    const dashLink = document.getElementById('navDashboard');
    const adminLink = document.getElementById('navAdmin');

    if (token) {
        if (loginLink) loginLink.style.display = 'none';
        if (logoutLink) logoutLink.style.display = 'inline';
        if (dashLink) dashLink.style.display = 'inline';
        if (adminLink && user.role === 'admin') adminLink.style.display = 'inline';
    } else {
        if (loginLink) loginLink.style.display = 'inline';
        if (logoutLink) logoutLink.style.display = 'none';
        if (dashLink) dashLink.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Run on every page load
document.addEventListener('DOMContentLoaded', updateNav);
