async function sendRequest(path, body) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The request could not be completed.');
  return result;
}

const loginForm = document.querySelector('#login-form');
const registerForm = document.querySelector('#register-form');
const message = document.querySelector('#form-message');

for (const form of [loginForm, registerForm]) {
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    message.textContent = '';
    message.classList.remove('error');
    const data = Object.fromEntries(new FormData(form));
    try {
      const endpoint = form.id === 'login-form' ? '/api/login' : '/api/register';
      const result = await sendRequest(endpoint, data);
      message.textContent = result.message;
      if (form.id === 'login-form') window.location.assign('/dashboard.html');
      if (form.id === 'register-form') window.setTimeout(() => window.location.assign('/login.html'), 700);
    } catch (error) {
      message.textContent = error.message;
      message.classList.add('error');
    }
  });
}

const accountEmail = document.querySelector('#account-email');
if (accountEmail) {
  fetch('/api/me')
    .then(async (response) => {
      if (!response.ok) throw new Error('Your session has ended. Please sign in again.');
      return response.json();
    })
    .then((user) => { accountEmail.textContent = user.email; })
    .catch((error) => { window.location.replace(`/login.html?message=${encodeURIComponent(error.message)}`); });
}

const logoutButton = document.querySelector('#logout-button');
logoutButton?.addEventListener('click', async () => {
  try {
    await fetch('/api/logout', { method: 'POST' });
    window.location.replace('/login.html');
  } catch (error) {
    const output = document.querySelector('#dashboard-message');
    output.textContent = `Could not sign out: ${error.message}`;
    output.classList.add('error');
  }
});

if (message) {
  const queryMessage = new URLSearchParams(window.location.search).get('message');
  if (queryMessage) {
    message.textContent = queryMessage;
    message.classList.add('error');
  }
}
