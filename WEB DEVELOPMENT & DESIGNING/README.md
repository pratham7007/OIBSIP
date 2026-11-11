# Web Development & Designing

The workspace contains the three Level 1 tasks, four Level 2 tasks, and the Level 3 full-stack pizza application from the OASIS INFOBYTE task list.

## Level 1

Open [Level 1/index.html](./Level%201/index.html) with a static web server. The pages are also available from the earlier local server at `http://localhost:8000`.

## Level 2

Install Node.js, then map the workspace to a drive letter for npm scripts (the track folder name contains an ampersand):

```powershell
subst W: "D:\Oasis\WEB DEVELOPMENT & DESIGNING"
cd W:\Level 2
npm install
npm start
```

Open `http://localhost:4173`. The login task uses a local Express API, scrypt password hashes, HTTP-only session cookies, and a JSON user store in `Level 2/data/users.json`. That file is generated on first registration and is intentionally not committed.

## Level 3

Requirements: Node.js, npm, and MongoDB Community running locally (or a MongoDB connection string you control).

1. Map the workspace to a drive letter as above, then copy `W:\Level 3\server\.env.example` to `W:\Level 3\server\.env`.
2. Set `JWT_SECRET`, `MONGODB_URI`, and an `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
3. Optionally add Razorpay **test-mode** credentials (`rzp_test_...`) and SMTP values. Without Razorpay credentials, development uses a clearly labeled local demo-payment confirmation; it never charges a card. Without SMTP, verification/reset URLs are printed only to the local server console.
4. In a terminal, run `npm install` in `W:\Level 3`, then `npm install` in `W:\Level 3\server` and `W:\Level 3\client`.
5. Start MongoDB, then run `npm run dev` in `Level 3`.
6. Open `http://localhost:5173`.

The admin account is seeded only from the configured environment variables; public registration cannot assign the admin role. Order status updates and inventory changes require that account. The application rejects non-test Razorpay key IDs.
