const API_BASE = '/api';

function getAccessToken() {
    return localStorage.getItem('access_token');
}

function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

function setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    if (refresh) {
        localStorage.setItem('refresh_token', refresh);
    }
}

function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

function redirectToLogin() {
    clearTokens();
    window.location.href = '/login/';
}

async function refreshAccessToken() {
    const refresh = getRefreshToken();
    if (!refresh) return false;

    const response = await fetch(`${API_BASE}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
    });

    if (!response.ok) return false;

    const data = await response.json();
    setTokens(data.access, null);
    return true;
}

async function apiFetch(path, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    const access = getAccessToken();
    if (access) {
        headers['Authorization'] = `Bearer ${access}`;
    }

    let response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            redirectToLogin();
            return null;
        }
        headers['Authorization'] = `Bearer ${getAccessToken()}`;
        response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }

    return response;
}

document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            redirectToLogin();
        });
    }
});