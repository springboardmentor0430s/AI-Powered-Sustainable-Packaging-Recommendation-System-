import { signup } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('signupForm');
  const status = document.getElementById('status');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = '';

    const companyName = form.companyName.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;

    if (!companyName || !email || !password) {
      status.textContent = 'Please fill all fields.';
      return;
    }
    if (password.length < 8) {
      status.textContent = 'Password must be at least 8 characters.';
      return;
    }

    try {
      await signup(email, password, companyName);
      status.textContent = 'Account created. Redirecting...';
      window.location.href = 'index.html';
    } catch (err) {
      status.textContent = `Signup failed: ${err.message}`;
    }
  });
});
