import nodemailer from 'nodemailer';

let transporter;
if (process.env.SMTP_HOST && process.env.SMTP_USER && process.env.SMTP_PASS) {
  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT ?? 587),
    secure: Number(process.env.SMTP_PORT ?? 587) === 465,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
  });
}

export async function sendMail({ to, subject, text, html }) {
  if (!transporter) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('SMTP must be configured to send email in production.');
    }
    console.info(`\n[Development email]\nTo: ${to}\nSubject: ${subject}\n${text}\n`);
    return;
  }
  await transporter.sendMail({
    from: process.env.MAIL_FROM ?? 'Crust & Craft <no-reply@example.com>',
    to,
    subject,
    text,
    html
  });
}

export async function sendLowStockAlert(items) {
  const to = process.env.ADMIN_ALERT_EMAIL;
  if (!to) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('ADMIN_ALERT_EMAIL must be configured to send low-stock notifications.');
    }
    console.info(`[Development low-stock alert]\n${items.map((item) => `${item.name}: ${item.stock} left (threshold ${item.threshold})`).join('\n')}`);
    return;
  }
  await sendMail({
    to,
    subject: 'Crust & Craft inventory is running low',
    text: items.map((item) => `${item.name}: ${item.stock} left (threshold ${item.threshold})`).join('\n')
  });
}
