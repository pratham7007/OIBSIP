import { useCallback, useEffect, useMemo, useState } from 'react';

const money = (rupees) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0
}).format(rupees);
const emailVerificationRequests = new Map();

async function api(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'The request could not be completed.');
  return data;
}

function App() {
  const [user, setUser] = useState(null);
  const [catalog, setCatalog] = useState([]);
  const [choices, setChoices] = useState({ base: [], sauce: [], cheese: [], vegetables: [] });
  const [stock, setStock] = useState({});
  const [selectedPizza, setSelectedPizza] = useState('');
  const [builder, setBuilder] = useState({ base: '', sauce: '', cheese: '', vegetables: [] });
  const [orders, setOrders] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [authMode, setAuthMode] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const selectedRecipe = useMemo(
    () => catalog.find((item) => item.id === selectedPizza),
    [catalog, selectedPizza]
  );

  const refreshOrders = useCallback(async () => {
    if (!user || user.role !== 'user') return;
    try {
      const result = await api('/api/orders');
      setOrders(result.orders);
    } catch (requestError) {
      setError(requestError.message);
    }
  }, [user]);

  const refreshAdmin = useCallback(async () => {
    if (!user || user.role !== 'admin') return;
    try {
      const [inventoryResult, ordersResult] = await Promise.all([
        api('/api/admin/inventory'),
        api('/api/admin/orders')
      ]);
      setInventory(inventoryResult.inventory);
      setOrders(ordersResult.orders);
    } catch (requestError) {
      setError(requestError.message);
    }
  }, [user]);

  useEffect(() => {
    let active = true;
    api('/api/catalog')
      .then((result) => {
        if (!active) return;
        setCatalog(result.catalog);
        setChoices(result.options);
        setStock(result.stock);
        setSelectedPizza(result.catalog[0]?.id ?? '');
        setBuilder({
          base: result.options.base[1]?.key ?? '',
          sauce: result.options.sauce[0]?.key ?? '',
          cheese: result.options.cheese[0]?.key ?? '',
          vegetables: []
        });
      })
      .catch((requestError) => { if (active) setError(requestError.message); });

    const query = new URLSearchParams(window.location.search);
    const verifyToken = query.get('verify');
    const resetToken = query.get('reset');
    if (verifyToken) {
      setBusy(true);
      if (!emailVerificationRequests.has(verifyToken)) {
        emailVerificationRequests.set(
          verifyToken,
          api('/api/auth/verify', { method: 'POST', body: JSON.stringify({ token: verifyToken }) })
        );
      }
      emailVerificationRequests.get(verifyToken)
        .then((result) => {
          if (!active) return;
          setUser(result.user);
          setMessage(result.message);
          window.history.replaceState({}, '', '/');
        })
        .catch((requestError) => { if (active) setError(requestError.message); })
        .finally(() => { if (active) setBusy(false); });
    } else if (resetToken) {
      setAuthMode('reset');
      window.history.replaceState({}, '', `/?reset=${encodeURIComponent(resetToken)}`);
    } else {
      api('/api/auth/me')
        .then((result) => { if (active && result.user) setUser(result.user); })
        .catch(() => {});
    }
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    if (user.role === 'admin') refreshAdmin();
    else refreshOrders();
    const timer = window.setInterval(() => {
      if (user.role === 'admin') refreshAdmin();
      else refreshOrders();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [user, refreshAdmin, refreshOrders]);

  const openAuth = (mode) => {
    setError('');
    setMessage('');
    setAuthMode(mode);
  };

  async function submitAuth(event) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setBusy(true);
    setError('');
    setMessage('');
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    try {
      if (authMode === 'register') {
        const result = await api('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
        setMessage(result.message);
        formElement.reset();
        return;
      }
      if (authMode === 'forgot') {
        const result = await api('/api/auth/forgot-password', { method: 'POST', body: JSON.stringify(payload) });
        setMessage(result.message);
        return;
      }
      if (authMode === 'reset') {
        payload.token = new URLSearchParams(window.location.search).get('reset');
        const result = await api('/api/auth/reset-password', { method: 'POST', body: JSON.stringify(payload) });
        setMessage(result.message);
        setAuthMode('login');
        window.history.replaceState({}, '', '/');
        return;
      }
      const endpoint = authMode === 'admin' ? '/api/auth/admin-login' : '/api/auth/login';
      const result = await api(endpoint, { method: 'POST', body: JSON.stringify(payload) });
      setUser(result.user);
      setAuthMode('');
      setMessage(`Welcome${result.user.name ? `, ${result.user.name}` : ''}.`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    try {
      await api('/api/auth/logout', { method: 'POST', body: '{}' });
      setUser(null);
      setOrders([]);
      setInventory([]);
      setMessage('You are signed out.');
      setError('');
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function toggleVegetable(key) {
    setBuilder((current) => ({
      ...current,
      vegetables: current.vegetables.includes(key)
        ? current.vegetables.filter((item) => item !== key)
        : [...current.vegetables, key]
    }));
  }

  async function loadCheckout() {
    if (window.Razorpay) return;
    await new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = resolve;
      script.onerror = () => reject(new Error('Could not load Razorpay Checkout. Check your connection and try again.'));
      document.body.append(script);
    });
  }

  async function placeOrder() {
    if (!user) {
      openAuth('login');
      setMessage('Sign in before placing your order.');
      return;
    }
    if (!selectedRecipe || !builder.base || !builder.sauce || !builder.cheese) {
      setError('Choose a pizza, base, sauce, and cheese to continue.');
      return;
    }
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const order = await api('/api/orders', {
        method: 'POST',
        body: JSON.stringify({ pizzaId: selectedRecipe.id, ...builder })
      });
      if (order.paymentMode === 'demo') {
        const confirmation = window.confirm(
          `Development payment for ${money(order.amount)}. No real charge will be made. Simulate a successful test payment?`
        );
        if (!confirmation) {
          setMessage('Demo checkout cancelled. Your pending order was not charged.');
          return;
        }
        await api('/api/payments/demo-success', {
          method: 'POST',
          body: JSON.stringify({ orderId: order.orderId })
        });
      } else {
        await loadCheckout();
        const checkout = new window.Razorpay({
          key: order.keyId,
          amount: order.amount,
          currency: order.currency,
          name: 'Crust & Craft',
          description: selectedRecipe.name,
          order_id: order.razorpayOrderId,
          prefill: { email: user.email, name: user.name },
          theme: { color: '#b94f2f' },
          handler: async (payment) => {
            try {
              await api('/api/payments/verify', {
                method: 'POST',
                body: JSON.stringify({
                  orderId: order.orderId,
                  razorpayOrderId: payment.razorpay_order_id,
                  razorpayPaymentId: payment.razorpay_payment_id,
                  razorpaySignature: payment.razorpay_signature
                })
              });
              setMessage('Payment confirmed. Your pizza is in the queue!');
              await refreshOrders();
            } catch (requestError) {
              setError(requestError.message);
            } finally {
              setBusy(false);
            }
          },
          modal: { ondismiss: () => setBusy(false) }
        });
        checkout.on('payment.failed', (failure) => {
          setError(failure.error?.description || 'Payment was not completed.');
          setBusy(false);
        });
        checkout.open();
        return;
      }
      setMessage('Payment confirmed. Your pizza is in the queue!');
      await refreshOrders();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  async function updateInventory(event, item) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    try {
      await api(`/api/admin/inventory/${encodeURIComponent(item.key)}`, {
        method: 'PATCH',
        body: JSON.stringify({ stock: values.get('stock'), threshold: values.get('threshold') })
      });
      setMessage(`${item.name} inventory updated.`);
      await refreshAdmin();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function updateStatus(order, status) {
    try {
      await api(`/api/admin/orders/${order._id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      });
      await refreshAdmin();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="logo" href="#" onClick={(event) => { event.preventDefault(); setUser(user); }}>CRUST <span>&</span> CRAFT</a>
        <nav className="topnav" aria-label="Main navigation">
          <a href="#menu">Menu</a><a href="#builder">Build a pizza</a>
          {user?.role === 'user' && <a href="#orders">Your orders</a>}
        </nav>
        <div className="top-actions">
          {user ? <><span className="user-email">{user.role === 'admin' ? 'Kitchen admin' : user.email}</span><button className="text-button" onClick={logout}>Sign out</button></>
            : <><button className="text-button" onClick={() => openAuth('login')}>Sign in</button><button className="button button-dark" onClick={() => openAuth('register')}>Create account</button></>}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-content">
            <span className="eyebrow"><i /> FRESH FROM OUR KITCHEN</span>
            <h1>A good day<br />starts with <em>pizza.</em></h1>
            <p>Slow-fermented dough, bright seasonal toppings, and the freedom to make it yours.</p>
            <div className="hero-buttons"><a className="button button-dark" href="#menu">Explore the menu <span>↘</span></a><span className="delivery-note">Made fresh · Delivered with care</span></div>
            <div className="hero-stats"><div><strong>48h</strong><span>slow dough</span></div><div><strong>100%</strong><span>real ingredients</span></div><div><strong>Made</strong><span>your way</span></div></div>
          </div>
          <div className="hero-visual" aria-label="Illustration of a fresh pizza">
            <div className="sunburst" /><div className="pizza-plate"><div className="pizza">
              <i className="topping t1" /><i className="topping t2" /><i className="topping t3" /><i className="topping t4" /><i className="topping t5" /><i className="topping t6" /><i className="leaf l1" /><i className="leaf l2" /><i className="leaf l3" />
            </div></div><span className="visual-note">THE GARDEN<br />MARGHERITA</span>
          </div>
        </section>

        <section className="menu-section section-wrap" id="menu">
          <div className="section-title"><div><span className="eyebrow">THE GOOD STUFF</span><h2>Find your new favorite.</h2></div><p>Thoughtful classics, made with ingredients worth slowing down for.</p></div>
          <div className="menu-grid">
            {catalog.map((pizza) => <article className={`menu-card ${pizza.accent}`} key={pizza.id}>
              <div className="menu-art"><span>{pizza.tag}</span><div className="mini-pizza"><i /><i /><i /><b>✳</b></div></div>
              <div className="menu-card-copy"><div><h3>{pizza.name}</h3><p>{pizza.description}</p></div><strong>{money(pizza.price)}</strong></div>
              <button className="link-button" onClick={() => { setSelectedPizza(pizza.id); document.querySelector('#builder')?.scrollIntoView({ behavior: 'smooth' }); }}>Customize yours <span>↗</span></button>
            </article>)}
          </div>
        </section>

        <section className="builder-section" id="builder">
          <div className="section-wrap">
            <div className="section-title"><div><span className="eyebrow">YOUR PIZZA, YOUR RULES</span><h2>Build your own.</h2></div><p>Pick your base, choose a sauce, make it cheesy, then add your favorite greens.</p></div>
            <div className="builder-layout">
              <div className="builder-steps">
                <fieldset className="builder-step"><legend><span>01</span> Choose your pizza</legend><div className="choice-row">
                  {catalog.map((pizza) => <button key={pizza.id} className={`choice-chip ${selectedPizza === pizza.id ? 'selected' : ''}`} onClick={() => setSelectedPizza(pizza.id)}>{pizza.name}</button>)}
                </div></fieldset>
                <fieldset className="builder-step"><legend><span>02</span> Choose a base</legend><div className="choice-grid">
                  {choices.base.map((option) => <label className="radio-card" key={option.key}><input type="radio" name="base" checked={builder.base === option.key} disabled={!stock[option.key]} onChange={() => setBuilder({ ...builder, base: option.key })} /><span>{option.name}<small>{stock[option.key] ?? 0} available</small></span></label>)}
                </div></fieldset>
                <fieldset className="builder-step"><legend><span>03</span> Choose a sauce</legend><div className="choice-row">
                  {choices.sauce.map((option) => <label className="choice-chip" key={option.key}><input type="radio" name="sauce" checked={builder.sauce === option.key} disabled={!stock[option.key]} onChange={() => setBuilder({ ...builder, sauce: option.key })} />{option.name}</label>)}
                </div></fieldset>
                <fieldset className="builder-step"><legend><span>04</span> Choose your cheese</legend><div className="choice-row">
                  {choices.cheese.map((option) => <label className="choice-chip" key={option.key}><input type="radio" name="cheese" checked={builder.cheese === option.key} disabled={!stock[option.key]} onChange={() => setBuilder({ ...builder, cheese: option.key })} />{option.name}</label>)}
                </div></fieldset>
                <fieldset className="builder-step"><legend><span>05</span> Add vegetables <small>(choose as many as you like)</small></legend><div className="choice-row">
                  {choices.vegetables.map((option) => <label className={`choice-chip ${builder.vegetables.includes(option.key) ? 'selected' : ''}`} key={option.key}><input type="checkbox" checked={builder.vegetables.includes(option.key)} disabled={!stock[option.key]} onChange={() => toggleVegetable(option.key)} />{option.name}</label>)}
                </div></fieldset>
              </div>
              <aside className="order-summary">
                <span className="eyebrow">ORDER SUMMARY</span><div className="summary-art"><div className="mini-pizza"><i /><i /><i /><b>✳</b></div></div>
                <h3>{selectedRecipe?.name ?? 'Your pizza'}</h3><p>{selectedRecipe?.description ?? 'Choose your pizza to begin.'}</p>
                <ul><li><span>Base</span><strong>{choices.base.find((item) => item.key === builder.base)?.name || 'Choose a base'}</strong></li>
                  <li><span>Sauce</span><strong>{choices.sauce.find((item) => item.key === builder.sauce)?.name || 'Choose a sauce'}</strong></li>
                  <li><span>Cheese</span><strong>{choices.cheese.find((item) => item.key === builder.cheese)?.name || 'Choose cheese'}</strong></li>
                  <li><span>Vegetables</span><strong>{builder.vegetables.map((key) => choices.vegetables.find((item) => item.key === key)?.name).filter(Boolean).join(', ') || 'None'}</strong></li></ul>
                <div className="summary-total"><span>Total</span><strong>{money(selectedRecipe?.price ?? 0)}</strong></div>
                <button className="button button-dark full-button" disabled={busy || !selectedRecipe} onClick={placeOrder}>{busy ? 'Please wait…' : 'Continue to payment'}</button>
                <p className="fine-print">Secure checkout · Razorpay test mode</p>
              </aside>
            </div>
          </div>
        </section>

        {user?.role === 'user' && <section className="orders-section section-wrap" id="orders">
          <div className="section-title"><div><span className="eyebrow">FRESH UPDATES</span><h2>Your orders.</h2></div><p>Order statuses refresh automatically.</p></div>
          {orders.length ? <div className="orders-grid">{orders.map((order) => <article className="order-card" key={order._id}>
            <div className="order-top"><div><span className="eyebrow">{order.status}</span><h3>{order.pizzaName}</h3></div><strong>{money(order.amount)}</strong></div>
            <p>{order.customization.base} · {order.customization.sauce} · {order.customization.cheese}</p>
            <div className="status-track">{['Order Received', 'In Kitchen', 'Sent to Delivery'].map((status) => <span className={['Order Received', 'In Kitchen', 'Sent to Delivery'].indexOf(order.status) >= ['Order Received', 'In Kitchen', 'Sent to Delivery'].indexOf(status) ? 'active' : ''} key={status}>{status}</span>)}</div>
          </article>)}</div> : <div className="empty-orders">Your next pizza story starts here.</div>}
        </section>}

        {user?.role === 'admin' && <section className="admin-section section-wrap">
          <div className="section-title"><div><span className="eyebrow">STORE OPERATIONS</span><h2>Kitchen dashboard.</h2></div><p>Inventory, stock thresholds, and live paid orders.</p></div>
          <h3 className="admin-heading">Inventory</h3>
          <div className="inventory-grid">{inventory.map((item) => <form className={`inventory-card ${item.stock < item.threshold ? 'low' : ''}`} key={item.key} onSubmit={(event) => updateInventory(event, item)}>
            <span className="eyebrow">{item.category}</span><strong>{item.name}</strong><label>Stock<input name="stock" type="number" min="0" step="1" defaultValue={item.stock} required /></label><label>Alert below<input name="threshold" type="number" min="0" step="1" defaultValue={item.threshold} required /></label><button className="button button-dark" type="submit">Save stock</button>
          </form>)}</div>
          <h3 className="admin-heading">Paid orders</h3>
          <div className="orders-grid">{orders.map((order) => <article className="order-card" key={order._id}><div className="order-top"><div><span className="eyebrow">{order.customerEmail}</span><h3>{order.pizzaName}</h3></div><strong>{money(order.amount)}</strong></div><p>{order.customization.base} · {order.customization.sauce} · {order.customization.cheese}</p><label className="status-select">Update status<select value={order.status} onChange={(event) => updateStatus(order, event.target.value)}>{['Order Received', 'In Kitchen', 'Sent to Delivery', 'Delivered'].map((status) => <option key={status}>{status}</option>)}</select></label></article>)}</div>
        </section>}

        <section className="story-section"><div className="section-wrap story-inner"><div><span className="eyebrow">A LITTLE MORE HUMAN</span><h2>Good food.<br /><em>Good feeling.</em></h2></div><p>We believe a great pizza is more than what goes on top. It’s a slow morning, a shared table, a reason to stay a little longer. Our kitchen keeps things seasonal, simple, and made with care.</p><span className="story-mark">✳</span></div></section>
      </main>
      <footer className="footer"><div className="section-wrap footer-inner"><a className="logo" href="#">CRUST <span>&</span> CRAFT</a><p>Made with care. Served with joy. · Test-mode project</p><a href="#menu">Back to top ↑</a></div></footer>

      {(message || error) && <div className={`toast ${error ? 'toast-error' : ''}`} role="status"><span>{error || message}</span><button onClick={() => { setError(''); setMessage(''); }} aria-label="Dismiss message">×</button></div>}

      {authMode && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setAuthMode(''); }}>
        <section className="auth-modal" aria-labelledby="auth-heading">
          <button className="close-modal" onClick={() => setAuthMode('')} aria-label="Close">×</button>
          <span className="eyebrow">{authMode === 'admin' ? 'KITCHEN ACCESS' : 'CRUST & CRAFT ACCOUNT'}</span>
          <h2 id="auth-heading">{authMode === 'register' ? 'Join the table.' : authMode === 'forgot' ? 'Find your way back.' : authMode === 'reset' ? 'Choose a new password.' : authMode === 'admin' ? 'Admin sign in.' : 'Welcome back.'}</h2>
          <p>{authMode === 'register' ? 'Create an account and verify your email to start ordering.' : authMode === 'forgot' ? 'We’ll send a reset link if an account matches.' : authMode === 'reset' ? 'Use at least eight characters and include a number.' : authMode === 'admin' ? 'This sign-in is reserved for the configured store administrator.' : 'Sign in for your orders and freshly baked updates.'}</p>
          <form onSubmit={submitAuth}>
            {authMode === 'register' && <label>Your name<input name="name" autoComplete="name" maxLength="80" required /></label>}
            {(authMode === 'login' || authMode === 'register' || authMode === 'forgot' || authMode === 'admin') && <label>Email<input name="email" type="email" autoComplete="email" required /></label>}
            {(authMode === 'login' || authMode === 'register' || authMode === 'reset' || authMode === 'admin') && <label>Password<input name="password" type="password" minLength="8" autoComplete={authMode === 'login' || authMode === 'admin' ? 'current-password' : 'new-password'} required /></label>}
            <button className="button button-dark full-button" disabled={busy}>{busy ? 'Please wait…' : authMode === 'register' ? 'Create account' : authMode === 'forgot' ? 'Send reset link' : authMode === 'reset' ? 'Update password' : 'Sign in'}</button>
          </form>
          {authMode === 'login' && <button className="modal-link" onClick={() => openAuth('forgot')}>Forgot password?</button>}
          {authMode === 'login' && <p className="modal-switch">New to the table? <button onClick={() => openAuth('register')}>Create account</button></p>}
          {authMode === 'register' && <p className="modal-switch">Already have an account? <button onClick={() => openAuth('login')}>Sign in</button></p>}
          {authMode === 'login' && <button className="admin-entry" onClick={() => openAuth('admin')}>Store administrator sign in</button>}
          {message && <p className="modal-message">{message}</p>}
          {error && <p className="modal-error" role="alert">{error}</p>}
        </section>
      </div>}
    </div>
  );
}

export default App;
