import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import express from 'express';

const scrypt = promisify(scryptCallback);
const root = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(root, 'public');
const dataDir = path.join(root, 'data');
const usersFile = path.join(dataDir, 'users.json');
const sessions = new Map();
const sessionLifetimeMs = 7 * 24 * 60 * 60 * 1000;
const app = express();

app.disable('x-powered-by');
app.use(express.json({ limit: '10kb' }));

async function loadUsers() {
  try {
    return JSON.parse(await readFile(usersFile, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return [];
    throw error;
  }
}

let writeQueue = Promise.resolve();
function saveUsers(users) {
  writeQueue = writeQueue.then(async () => {
    await mkdir(dataDir, { recursive: true });
    const temporaryFile = `${usersFile}.tmp`;
    await writeFile(temporaryFile, JSON.stringify(users, null, 2), 'utf8');
    await rename(temporaryFile, usersFile);
  });
  return writeQueue;
}

let registrationQueue = Promise.resolve();
function registerUser(email, password) {
  const registration = registrationQueue.then(async () => {
    const users = await loadUsers();
    if (users.some((user) => user.email === email)) return false;
    const salt = randomBytes(16);
    const hash = await scrypt(password, salt, 64);
    users.push({
      id: randomBytes(16).toString('hex'),
      email,
      passwordSalt: salt.toString('hex'),
      passwordHash: hash.toString('hex'),
      createdAt: new Date().toISOString()
    });
    await saveUsers(users);
    return true;
  });
  registrationQueue = registration.then(() => undefined, () => undefined);
  return registration;
}

function readCookie(request, name) {
  const cookies = request.headers.cookie?.split(';') ?? [];
  for (const cookie of cookies) {
    const [key, ...valueParts] = cookie.trim().split('=');
    if (key === name) return decodeURIComponent(valueParts.join('='));
  }
  return null;
}

function findSession(request) {
  const token = readCookie(request, 'oasis_session');
  if (!token) return null;
  const session = sessions.get(token);
  if (!session || session.expiresAt <= Date.now()) {
    sessions.delete(token);
    return null;
  }
  return session;
}

function requireSession(request, response, next) {
  const session = findSession(request);
  if (!session) {
    response.redirect('/login.html');
    return;
  }
  request.session = session;
  next();
}

app.post('/api/register', async (request, response, next) => {
  try {
    const email = String(request.body.email ?? '').trim().toLowerCase();
    const password = String(request.body.password ?? '');
    if (!email || !password) {
      response.status(400).json({ error: 'Email and password are required.' });
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      response.status(400).json({ error: 'Enter a valid email address.' });
      return;
    }
    if (password.length < 8 || !/\d/.test(password)) {
      response.status(400).json({ error: 'Use at least 8 characters and include at least one number.' });
      return;
    }

    if (!await registerUser(email, password)) {
      response.status(409).json({ error: 'An account with that email already exists.' });
      return;
    }

    response.status(201).json({ message: 'Account created. You can now sign in.' });
  } catch (error) {
    next(error);
  }
});

app.post('/api/login', async (request, response, next) => {
  try {
    const email = String(request.body.email ?? '').trim().toLowerCase();
    const password = String(request.body.password ?? '');
    if (!email || !password) {
      response.status(400).json({ error: 'Email and password are required.' });
      return;
    }

    const users = await loadUsers();
    const user = users.find((item) => item.email === email);
    let valid = false;
    if (user) {
      const actualHash = await scrypt(password, Buffer.from(user.passwordSalt, 'hex'), 64);
      valid = timingSafeEqual(actualHash, Buffer.from(user.passwordHash, 'hex'));
    }
    if (!valid) {
      response.status(401).json({ error: 'Email or password is incorrect.' });
      return;
    }

    const token = randomBytes(32).toString('base64url');
    sessions.set(token, {
      userId: user.id,
      email: user.email,
      expiresAt: Date.now() + sessionLifetimeMs
    });
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    response.setHeader(
      'Set-Cookie',
      `oasis_session=${encodeURIComponent(token)}; HttpOnly; SameSite=Lax; Path=/; Max-Age=${sessionLifetimeMs / 1000}${secure}`
    );
    response.json({ message: 'Signed in.' });
  } catch (error) {
    next(error);
  }
});

app.get('/api/me', (request, response) => {
  const session = findSession(request);
  if (!session) {
    response.status(401).json({ error: 'Sign in required.' });
    return;
  }
  response.json({ email: session.email });
});

app.post('/api/logout', (request, response) => {
  const token = readCookie(request, 'oasis_session');
  if (token) sessions.delete(token);
  response.setHeader('Set-Cookie', 'oasis_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0');
  response.json({ message: 'Signed out.' });
});

app.get('/dashboard.html', requireSession, (request, response) => {
  response.sendFile(path.join(publicDir, 'dashboard.html'));
});

app.use(express.static(publicDir));
app.use((error, request, response, next) => {
  console.error(error);
  if (response.headersSent) {
    next(error);
    return;
  }
  response.status(500).json({ error: 'The request could not be completed.' });
});

const port = Number(process.env.PORT ?? 4173);
app.listen(port, () => {
  console.log(`Level 2 tasks available at http://localhost:${port}`);
});
