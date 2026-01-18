import { login } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  const status = document.getElementById('status');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = '';

    const email = form.email.value.trim();
    const password = form.password.value;

    if (!email || !password) {
      status.textContent = 'Please enter your email and password.';
      return;
    }

    try {
      await login(email, password);
      status.textContent = 'Login successful. Redirecting...';
      window.location.href = 'index.html';
    } catch (err) {
      status.textContent = `Login failed: ${err.message}`;
    }
  });
});
