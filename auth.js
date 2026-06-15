// ==========================================================================
// LuxStay Authentication Page Logic (Login / Sign Up)
// ==========================================================================

// Tabs
const tabLogin = document.getElementById('tab-login');
const tabSignup = document.getElementById('tab-signup');

// Forms
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');

// Switch links inside forms
const switchToSignup = document.getElementById('switch-to-signup');
const switchToLogin = document.getElementById('switch-to-login');

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    checkExistingSession();
    setupEventListeners();
});

// If the visitor already has an active session, skip straight to the dashboard
async function checkExistingSession() {
    try {
        const response = await fetch('/api/session', { credentials: 'include' });
        if (!response.ok) return;
        const data = await response.json();
        if (data.authenticated) {
            window.location.href = '/';
        }
    } catch (err) {
        // If the session check fails, just stay on the login page silently.
    }
}

// ==========================================================================
// Tab Switching
// ==========================================================================

function showLoginTab() {
    tabLogin.classList.add('active');
    tabLogin.setAttribute('aria-selected', 'true');
    tabSignup.classList.remove('active');
    tabSignup.setAttribute('aria-selected', 'false');

    loginForm.classList.add('active');
    signupForm.classList.remove('active');
}

function showSignupTab() {
    tabSignup.classList.add('active');
    tabSignup.setAttribute('aria-selected', 'true');
    tabLogin.classList.remove('active');
    tabLogin.setAttribute('aria-selected', 'false');

    signupForm.classList.add('active');
    loginForm.classList.remove('active');
}

// ==========================================================================
// Form Submission
// ==========================================================================

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    const submitBtn = loginForm.querySelector('.auth-submit');
    setButtonLoading(submitBtn, true, 'Logging in...');

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Login failed.');
        }

        showToast('Login successful! Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 600);
    } catch (error) {
        showToast(error.message, 'error');
        setButtonLoading(submitBtn, false, 'Login');
    }
});

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const fullName = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;

    if (password !== confirmPassword) {
        showToast('Passwords do not match.', 'error');
        return;
    }

    if (password.length < 6) {
        showToast('Password must be at least 6 characters long.', 'error');
        return;
    }

    const submitBtn = signupForm.querySelector('.auth-submit');
    setButtonLoading(submitBtn, true, 'Creating account...');

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ full_name: fullName, email, password })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || 'Registration failed.');
        }

        showToast('Account created successfully! Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 600);
    } catch (error) {
        showToast(error.message, 'error');
        setButtonLoading(submitBtn, false, 'Create Account');
    }
});

// ==========================================================================
// Helpers
// ==========================================================================

function setButtonLoading(button, isLoading, label) {
    button.disabled = isLoading;
    button.querySelector('.btn-text').textContent = label;
}

function setupEventListeners() {
    tabLogin.addEventListener('click', showLoginTab);
    tabSignup.addEventListener('click', showSignupTab);

    switchToSignup.addEventListener('click', (e) => {
        e.preventDefault();
        showSignupTab();
    });

    switchToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginTab();
    });
}

// ==========================================================================
// Custom Notification Toast System (shared style with dashboard)
// ==========================================================================

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = type === 'success'
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #10b981"><polyline points="20 6 9 17 4 12"></polyline></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #ef4444"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;

    toast.innerHTML = `
        ${icon}
        <span class="toast-message">${message}</span>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}
