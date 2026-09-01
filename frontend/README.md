# GovernAI Frontend

React + Vite UI for the GovernAI platform. Talks directly to the FastAPI
backend (no separate Node/Express layer) — in dev, requests to `/api/*` are
proxied to `http://localhost:8000` (see `vite.config.js`); the backend also
has CORS enabled for `http://localhost:5173` if you call it directly.

## Pages

- **Reports** (`/`) — table of all governance reports with risk/decision/status badges
- **Submit use case** (`/submit`) — intake form; runs the full agent pipeline on submit
- **Report detail** (`/use-cases/:id`) — risk assessment, policy compliance, decision,
  and an approve/reject panel when a report is `pending_human_approval`

## Setup

```bash
npm install
cp .env.example .env.local   # optional: Firebase web config
npm run dev
# -> http://localhost:5173
```

The backend must be running separately (see the root [README](../README.md))
for the app to have any data to show.

## Authentication

Sign-in uses [Firebase Authentication](https://firebase.google.com/docs/auth)
(email/password + Google). Fill `.env.local` with the web app config from the
Firebase console (Project settings → General → Your apps → Web app):

```
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

`src/firebase.js` initialises the SDK, `src/auth.js` wraps sign-in/sign-up/
sign-out, and `src/api.js` attaches the user's ID token to every backend
request as `Authorization: Bearer <token>`.

If those variables are missing the UI runs in **demo mode**: the sign-in
screen accepts anything and no token is sent — the same behaviour as before
Firebase was wired in, so the UI can still be run standalone.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with HMR |
| `npm run build` | Type/lint-free production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Run Oxlint |
