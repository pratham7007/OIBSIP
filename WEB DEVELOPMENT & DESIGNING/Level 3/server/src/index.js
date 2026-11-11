import 'dotenv/config';
import { randomBytes, createHash, createHmac, timingSafeEqual } from 'node:crypto';
import bcrypt from 'bcryptjs';
import cookieParser from 'cookie-parser';
import express from 'express';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import jwt from 'jsonwebtoken';
import cron from 'node-cron';
import Razorpay from 'razorpay';
import { connectDatabase, Inventory, Order, User } from './database.js';
import { sendLowStockAlert, sendMail } from './mail.js';

const app = express();
const port = Number(process.env.PORT ?? 4000);
const clientUrl = process.env.CLIENT_URL ?? 'http://localhost:5173';
const jwtSecret = process.env.JWT_SECRET || (process.env.NODE_ENV === 'production' ? '' : randomBytes(32).toString('hex'));
const razorpayKeyId = process.env.RAZORPAY_KEY_ID ?? '';
const razorpayKeySecret = process.env.RAZORPAY_KEY_SECRET ?? '';
const razorpayEnabled = razorpayKeyId.startsWith('rzp_test_') && Boolean(razorpayKeySecret);
const razorpay = razorpayEnabled ? new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret }) : null;
const allowedStatuses = ['Order Received', 'In Kitchen', 'Sent to Delivery', 'Delivered'];
const catalog = [
  { id: 'margherita', name: 'Garden Margherita', description: 'Tomato, mozzarella, basil, and a little olive oil.', price: 799, accent: 'tomato', tag: 'Classic' },
  { id: 'smoky', name: 'Smoky Garden', description: 'Smoky BBQ, peppers, red onion, and smoked cheese.', price: 999, accent: 'orange', tag: 'Popular' },
  { id: 'green', name: 'Greenhouse', description: 'Pesto, spinach, mushrooms, olives, and mozzarella.', price: 949, accent: 'green', tag: 'Fresh' }
];
const options = {
  base: [
    { key: 'base-thin', name: 'Thin crust' }, { key: 'base-classic', name: 'Classic crust' },
    { key: 'base-pan', name: 'Pan crust' }, { key: 'base-wholewheat', name: 'Whole wheat crust' },
    { key: 'base-glutenfree', name: 'Gluten-free crust' }
  ],
  sauce: [
    { key: 'sauce-tomato', name: 'Roasted tomato' }, { key: 'sauce-pesto', name: 'Basil pesto' },
    { key: 'sauce-bbq', name: 'Smoky BBQ' }, { key: 'sauce-white', name: 'Garlic cream' },
    { key: 'sauce-spicy', name: 'Spicy arrabbiata' }
  ],
  cheese: [
    { key: 'cheese-mozzarella', name: 'Mozzarella' }, { key: 'cheese-vegan', name: 'Plant-based' },
    { key: 'cheese-smoked', name: 'Smoked cheese' }
  ],
  vegetables: [
    { key: 'veg-mushroom', name: 'Mushrooms' }, { key: 'veg-pepper', name: 'Bell peppers' },
    { key: 'veg-onion', name: 'Red onion' }, { key: 'veg-olive', name: 'Olives' },
    { key: 'veg-spinach', name: 'Baby spinach' }, { key: 'veg-tomato', name: 'Cherry tomatoes' }
  ]
};

app.disable('x-powered-by');
app.use(helmet({
  crossOriginResourcePolicy: { policy: 'cross-origin' },
  contentSecurityPolicy: {
    directives: {
      ...helmet.contentSecurityPolicy.getDefaultDirectives(),
      'connect-src': ["'self'", 'https://api.razorpay.com'],
      'font-src': ["'self'", 'https://fonts.gstatic.com'],
      'frame-src': ["'self'", 'https://api.razorpay.com'],
      'script-src': ["'self'", 'https://checkout.razorpay.com'],
      'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com']
    }
  }
}));
app.use(express.json({ limit: '20kb' }));
app.use(cookieParser());
app.use((request, response, next) => {
  response.setHeader('Access-Control-Allow-Origin', clientUrl);
  response.setHeader('Access-Control-Allow-Credentials', 'true');
  response.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  response.setHeader('Access-Control-Allow-Methods', 'GET,POST,PATCH,OPTIONS');
  if (request.method === 'OPTIONS') {
    response.sendStatus(204);
    return;
  }
  next();
});

const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, limit: 12, standardHeaders: 'draft-8', legacyHeaders: false });
const digest = (token) => createHash('sha256').update(token).digest('hex');
const makeToken = () => randomBytes(32).toString('base64url');
const emailIsValid = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

function setAuthCookie(response, user) {
  const token = jwt.sign({ sub: user.id, role: user.role }, jwtSecret, { expiresIn: '7d' });
  response.cookie('oasis_pizza_session', token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    maxAge: 7 * 24 * 60 * 60 * 1000,
    path: '/'
  });
}

async function authenticate(request, response, next) {
  try {
    const token = request.cookies.oasis_pizza_session;
    if (!token) {
      response.status(401).json({ error: 'Please sign in to continue.' });
      return;
    }
    const payload = jwt.verify(token, jwtSecret);
    const user = await User.findById(payload.sub).select('_id name email role verifiedAt');
    if (!user || !user.verifiedAt) {
      response.status(401).json({ error: 'Please verify your email and sign in again.' });
      return;
    }
    request.user = user;
    next();
  } catch (error) {
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      response.status(401).json({ error: 'Your session has ended. Please sign in again.' });
      return;
    }
    next(error);
  }
}

function requireAdmin(request, response, next) {
  if (request.user.role !== 'admin') {
    response.status(403).json({ error: 'Admin access is required.' });
    return;
  }
  next();
}

function safeUser(user) {
  return { id: user.id, name: user.name, email: user.email, role: user.role };
}

app.get('/api/health', (request, response) => response.json({ status: 'ok', paymentMode: razorpayEnabled ? 'razorpay-test' : 'development-demo' }));
app.get('/api/catalog', async (request, response, next) => {
  try {
    const stock = await Inventory.find({}, 'key stock');
    response.json({ catalog, options, stock: Object.fromEntries(stock.map((item) => [item.key, item.stock])) });
  } catch (error) { next(error); }
});

app.post('/api/auth/register', authLimiter, async (request, response, next) => {
  try {
    const name = String(request.body.name ?? '').trim();
    const email = String(request.body.email ?? '').trim().toLowerCase();
    const password = String(request.body.password ?? '');
    if (!emailIsValid(email) || password.length < 8 || !/\d/.test(password)) {
      response.status(400).json({ error: 'Use a valid email and a password of at least 8 characters with a number.' });
      return;
    }
    if (name.length > 80) {
      response.status(400).json({ error: 'Name must be 80 characters or fewer.' });
      return;
    }
    if (await User.exists({ email })) {
      response.status(409).json({ error: 'An account with that email already exists.' });
      return;
    }
    const token = makeToken();
    const user = await User.create({
      name, email, passwordHash: await bcrypt.hash(password, 12),
      verificationTokenHash: digest(token), verificationExpiresAt: new Date(Date.now() + 60 * 60 * 1000)
    });
    const link = `${clientUrl}/?verify=${encodeURIComponent(token)}`;
    try {
      await sendMail({
        to: email, subject: 'Verify your Crust & Craft account',
        text: `Hello ${name || 'there'}, verify your email within one hour: ${link}`
      });
    } catch (error) {
      await User.deleteOne({ _id: user.id, verificationTokenHash: digest(token) });
      throw error;
    }
    response.status(201).json({ message: 'Account created. Follow the verification link sent to your email.' });
  } catch (error) { next(error); }
});

app.post('/api/auth/verify', authLimiter, async (request, response, next) => {
  try {
    const token = String(request.body.token ?? '');
    if (!token) {
      response.status(400).json({ error: 'Verification token is required.' });
      return;
    }
    const user = await User.findOne({
      verificationTokenHash: digest(token),
      verificationExpiresAt: { $gt: new Date() }
    });
    if (!user) {
      response.status(400).json({ error: 'This verification link is invalid or has expired.' });
      return;
    }
    user.verifiedAt = new Date();
    user.verificationTokenHash = null;
    user.verificationExpiresAt = null;
    await user.save();
    setAuthCookie(response, user);
    response.json({ user: safeUser(user), message: 'Email verified. You are signed in.' });
  } catch (error) { next(error); }
});

app.post('/api/auth/login', authLimiter, async (request, response, next) => {
  try {
    const email = String(request.body.email ?? '').trim().toLowerCase();
    const password = String(request.body.password ?? '');
    if (!email || !password) {
      response.status(400).json({ error: 'Email and password are required.' });
      return;
    }
    const user = await User.findOne({ email });
    const valid = user ? await bcrypt.compare(password, user.passwordHash) : false;
    if (!valid) {
      response.status(401).json({ error: 'Email or password is incorrect.' });
      return;
    }
    if (!user.verifiedAt) {
      response.status(403).json({ error: 'Verify your email before signing in.' });
      return;
    }
    setAuthCookie(response, user);
    response.json({ user: safeUser(user) });
  } catch (error) { next(error); }
});

app.post('/api/auth/admin-login', authLimiter, async (request, response, next) => {
  try {
    const email = String(request.body.email ?? '').trim().toLowerCase();
    const password = String(request.body.password ?? '');
    const user = await User.findOne({ email, role: 'admin' });
    if (!user || !await bcrypt.compare(password, user.passwordHash)) {
      response.status(401).json({ error: 'Email or password is incorrect.' });
      return;
    }
    setAuthCookie(response, user);
    response.json({ user: safeUser(user) });
  } catch (error) { next(error); }
});

app.post('/api/auth/forgot-password', authLimiter, async (request, response, next) => {
  try {
    const email = String(request.body.email ?? '').trim().toLowerCase();
    if (emailIsValid(email)) {
      const user = await User.findOne({ email });
      if (user) {
        const token = makeToken();
        user.resetTokenHash = digest(token);
        user.resetExpiresAt = new Date(Date.now() + 30 * 60 * 1000);
        await user.save();
        const link = `${clientUrl}/?reset=${encodeURIComponent(token)}`;
        await sendMail({ to: email, subject: 'Reset your Crust & Craft password', text: `Reset your password within 30 minutes: ${link}` });
      }
    }
    response.json({ message: 'If that account exists, a password reset link has been sent.' });
  } catch (error) { next(error); }
});

app.post('/api/auth/reset-password', authLimiter, async (request, response, next) => {
  try {
    const token = String(request.body.token ?? '');
    const password = String(request.body.password ?? '');
    if (!token || password.length < 8 || !/\d/.test(password)) {
      response.status(400).json({ error: 'Use a password of at least 8 characters that includes a number.' });
      return;
    }
    const user = await User.findOne({ resetTokenHash: digest(token), resetExpiresAt: { $gt: new Date() } });
    if (!user) {
      response.status(400).json({ error: 'This password reset link is invalid or has expired.' });
      return;
    }
    user.passwordHash = await bcrypt.hash(password, 12);
    user.resetTokenHash = null;
    user.resetExpiresAt = null;
    await user.save();
    response.json({ message: 'Password updated. You can now sign in.' });
  } catch (error) { next(error); }
});

app.get('/api/auth/me', async (request, response, next) => {
  if (!request.cookies.oasis_pizza_session) {
    response.json({ user: null });
    return;
  }
  try {
    const payload = jwt.verify(request.cookies.oasis_pizza_session, jwtSecret);
    const user = await User.findById(payload.sub).select('_id name email role verifiedAt');
    response.json({ user: user?.verifiedAt ? safeUser(user) : null });
  } catch (error) {
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      response.json({ user: null });
      return;
    }
    next(error);
  }
});
app.post('/api/auth/logout', (request, response) => {
  response.clearCookie('oasis_pizza_session', { httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/' });
  response.json({ message: 'Signed out.' });
});

function buildOrderSelection(body) {
  const base = options.base.find((item) => item.key === body.base);
  const sauce = options.sauce.find((item) => item.key === body.sauce);
  const cheese = options.cheese.find((item) => item.key === body.cheese);
  const vegetables = Array.isArray(body.vegetables)
    ? options.vegetables.filter((item) => body.vegetables.includes(item.key))
    : [];
  const pizza = catalog.find((item) => item.id === body.pizzaId);
  if (!base || !sauce || !cheese || !pizza || vegetables.length !== new Set(body.vegetables ?? []).size) return null;
  return {
    pizza,
    customization: { base: base.name, sauce: sauce.name, cheese: cheese.name, vegetables: vegetables.map((item) => item.name) },
    inventoryKeys: [base.key, sauce.key, cheese.key, ...vegetables.map((item) => item.key)]
  };
}

async function createPendingOrder(request, response, next) {
  try {
    const selection = buildOrderSelection(request.body);
    if (!selection) {
      response.status(400).json({ error: 'Choose a valid pizza, base, sauce, cheese, and vegetable selection.' });
      return;
    }
    const inventory = await Inventory.find({ key: { $in: selection.inventoryKeys } });
    if (inventory.length !== selection.inventoryKeys.length || inventory.some((item) => item.stock < 1)) {
      response.status(409).json({ error: 'One or more selected ingredients are currently unavailable.' });
      return;
    }
    const order = await Order.create({
      user: request.user.id, customerEmail: request.user.email, pizzaName: selection.pizza.name,
      customization: selection.customization, inventoryKeys: selection.inventoryKeys, amount: selection.pizza.price
    });

    if (!razorpay) {
      if (process.env.NODE_ENV === 'production') {
        await order.deleteOne();
        response.status(503).json({ error: 'Razorpay test credentials are not configured.' });
        return;
      }
      order.paymentOrderId = `demo_${order.id}`;
      await order.save();
      response.status(201).json({
        orderId: order.id, paymentMode: 'demo', amount: order.amount, currency: order.currency,
        message: 'Development demo payment is enabled. No real payment will be taken.'
      });
      return;
    }

    const paymentOrder = await razorpay.orders.create({
      amount: order.amount * 100, currency: order.currency, receipt: order.id
    });
    order.paymentOrderId = paymentOrder.id;
    await order.save();
    response.status(201).json({
      orderId: order.id, paymentMode: 'razorpay-test', razorpayOrderId: paymentOrder.id,
      keyId: razorpayKeyId, amount: paymentOrder.amount, currency: paymentOrder.currency
    });
  } catch (error) { next(error); }
}

async function commitInventory(order) {
  const changed = [];
  for (const key of order.inventoryKeys) {
    const updated = await Inventory.findOneAndUpdate(
      { key, stock: { $gte: 1 } }, { $inc: { stock: -1 } }, { new: true }
    );
    if (!updated) {
      for (const previousKey of changed) await Inventory.updateOne({ key: previousKey }, { $inc: { stock: 1 } });
      return false;
    }
    changed.push(key);
  }
  return true;
}

async function confirmPayment(order, paymentId, response) {
  const claimed = await Order.findOneAndUpdate(
    { _id: order.id, paymentStatus: 'pending' },
    { $set: { paymentStatus: 'processing', paymentId } },
    { new: true }
  );
  if (!claimed) {
    const fresh = await Order.findById(order.id);
    if (fresh?.paymentStatus === 'paid') {
      response.json({ order: fresh });
      return;
    }
    response.status(409).json({ error: 'This payment is already being processed or cannot be confirmed.' });
    return;
  }
  const committed = await commitInventory(claimed);
  if (!committed) {
    let refundMessage = 'Please contact support about your payment.';
    if (razorpay && !String(paymentId).startsWith('demo_')) {
      const refund = await razorpay.payments.refund(paymentId, { amount: order.amount * 100 });
      refundMessage = `A refund was requested (${refund.id}).`;
    }
    claimed.paymentStatus = 'failed';
    await claimed.save();
    response.status(409).json({ error: `An ingredient just sold out. ${refundMessage}` });
    return;
  }
  claimed.paymentStatus = 'paid';
  claimed.inventoryCommittedAt = new Date();
  await claimed.save();
  response.json({ order: claimed });
}

app.post('/api/orders', authenticate, createPendingOrder);
app.post('/api/payments/demo-success', authenticate, async (request, response, next) => {
  try {
    if (process.env.NODE_ENV === 'production' || razorpay) {
      response.status(404).json({ error: 'Demo payments are not available.' });
      return;
    }
    const order = await Order.findOne({ _id: request.body.orderId, user: request.user.id, paymentStatus: 'pending' });
    if (!order || order.paymentOrderId !== `demo_${order.id}`) {
      response.status(404).json({ error: 'Pending demo order was not found.' });
      return;
    }
    await confirmPayment(order, `demo_payment_${order.id}`, response);
  } catch (error) { next(error); }
});

app.post('/api/payments/verify', authenticate, async (request, response, next) => {
  try {
    if (!razorpay) {
      response.status(503).json({ error: 'Razorpay test credentials are not configured.' });
      return;
    }
    const { orderId, razorpayOrderId, razorpayPaymentId, razorpaySignature } = request.body;
    const order = await Order.findOne({ _id: orderId, user: request.user.id, paymentStatus: 'pending' });
    if (!order || order.paymentOrderId !== razorpayOrderId) {
      response.status(404).json({ error: 'Pending payment order was not found.' });
      return;
    }
    const expected = createHmac('sha256', razorpayKeySecret).update(`${razorpayOrderId}|${razorpayPaymentId}`).digest();
    const supplied = Buffer.from(String(razorpaySignature ?? ''), 'hex');
    if (expected.length !== supplied.length || !timingSafeEqual(expected, supplied)) {
      response.status(400).json({ error: 'Payment signature could not be verified.' });
      return;
    }
    await confirmPayment(order, razorpayPaymentId, response);
  } catch (error) { next(error); }
});

app.get('/api/orders', authenticate, async (request, response, next) => {
  try {
    const orders = await Order.find({ user: request.user.id, paymentStatus: 'paid' }).sort({ createdAt: -1 }).limit(50);
    response.json({ orders });
  } catch (error) { next(error); }
});

app.get('/api/admin/inventory', authenticate, requireAdmin, async (request, response, next) => {
  try { response.json({ inventory: await Inventory.find().sort({ category: 1, name: 1 }) }); }
  catch (error) { next(error); }
});

app.patch('/api/admin/inventory/:key', authenticate, requireAdmin, async (request, response, next) => {
  try {
    const stock = Number(request.body.stock);
    const threshold = Number(request.body.threshold);
    if (!Number.isInteger(stock) || stock < 0 || !Number.isInteger(threshold) || threshold < 0) {
      response.status(400).json({ error: 'Stock and threshold must be non-negative whole numbers.' });
      return;
    }
    const item = await Inventory.findOneAndUpdate(
      { key: request.params.key },
      { $set: { stock, threshold, lowStockNotified: false } },
      { new: true, runValidators: true }
    );
    if (!item) {
      response.status(404).json({ error: 'Inventory item not found.' });
      return;
    }
    response.json({ item });
  } catch (error) { next(error); }
});

app.get('/api/admin/orders', authenticate, requireAdmin, async (request, response, next) => {
  try {
    const orders = await Order.find({ paymentStatus: 'paid' }).sort({ createdAt: -1 }).limit(100);
    response.json({ orders });
  } catch (error) { next(error); }
});

app.patch('/api/admin/orders/:id/status', authenticate, requireAdmin, async (request, response, next) => {
  try {
    const status = String(request.body.status ?? '');
    if (!allowedStatuses.includes(status)) {
      response.status(400).json({ error: 'Choose a valid order status.' });
      return;
    }
    const order = await Order.findOneAndUpdate(
      { _id: request.params.id, paymentStatus: 'paid' }, { $set: { status } }, { new: true }
    );
    if (!order) {
      response.status(404).json({ error: 'Paid order not found.' });
      return;
    }
    response.json({ order });
  } catch (error) { next(error); }
});

app.use((error, request, response, next) => {
  console.error(error);
  if (response.headersSent) {
    next(error);
    return;
  }
  if (error.code === 11000) {
    response.status(409).json({ error: 'That account already exists.' });
    return;
  }
  response.status(500).json({ error: 'The request could not be completed.' });
});

cron.schedule('* * * * *', async () => {
  try {
    const lowItems = await Inventory.find({ $expr: { $lt: ['$stock', '$threshold'] }, lowStockNotified: false });
    if (lowItems.length) {
      await sendLowStockAlert(lowItems);
      await Inventory.updateMany({ _id: { $in: lowItems.map((item) => item.id) } }, { $set: { lowStockNotified: true } });
    }
    await Inventory.updateMany(
      { $expr: { $gte: ['$stock', '$threshold'] }, lowStockNotified: true },
      { $set: { lowStockNotified: false } }
    );
  } catch (error) {
    console.error('Scheduled low-stock check failed:', error);
  }
});

const mongoUri = process.env.MONGODB_URI ?? 'mongodb://127.0.0.1:27017/oasis_pizza';
if (!mongoUri) throw new Error('MONGODB_URI must be configured.');
if (process.env.NODE_ENV === 'production' && jwtSecret.length < 32) throw new Error('Set JWT_SECRET to at least 32 characters in production.');
if (razorpayKeyId && !razorpayKeyId.startsWith('rzp_test_')) throw new Error('Only Razorpay test-mode key IDs (rzp_test_...) are accepted.');
if (!razorpayEnabled && process.env.NODE_ENV === 'production') throw new Error('Razorpay test credentials are required in production.');
if (!process.env.JWT_SECRET && process.env.NODE_ENV !== 'production') {
  console.warn('Using a temporary development JWT secret; sessions will expire when the API restarts.');
}
try {
  await connectDatabase(mongoUri, process.env.ADMIN_EMAIL, process.env.ADMIN_PASSWORD);
  app.listen(port, () => {
    console.log(`Pizza API listening on http://localhost:${port}`);
    if (!process.env.ADMIN_EMAIL || !process.env.ADMIN_PASSWORD) {
      console.warn('Admin account is disabled until ADMIN_EMAIL and ADMIN_PASSWORD are configured.');
    }
    if (!razorpayEnabled) console.warn('Development demo payments enabled; no real charge will be made.');
  });
} catch (error) {
  console.error('Could not start the pizza API:', error);
  process.exitCode = 1;
}
