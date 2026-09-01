# GovernAI Frontend

React + Vite UI for the GovernAI platform. Talks directly to the FastAPI
backend (no separate Node/Express layer) — in dev, requests to `/api/*` are
proxied to `http://localhost:8000` (see `vite.config.js`); the backend also
has CORS enabled for `http://localhost:5173` if you call it directly.

## Pages

- **Login** (`/login`) — email/password sign-in (Firebase Authentication)
- **Sign up** (`/signup`) — create an account with email/password
- **Reports** (`/`) — table of all governance reports with risk/decision/status badges
- **Submit use case** (`/submit`) — intake form; runs the full agent pipeline on submit
- **Report detail** (`/use-cases/:id`) — risk assessment, policy compliance, decision,
  and an approve/reject panel when a report is `pending_human_approval`

## Setup

```bash
npm install
cp .env.example .env   # then fill in your Firebase values
npm run dev
# -> http://localhost:5173
```

The backend must be running separately (see the root [README](../README.md))
for the app to have any data to show.

## Authentication

The UI is gated by **Firebase Authentication** (Email/Password) using the
modular Firebase JS SDK. Every route except `/login` and `/signup` is wrapped
in `ProtectedRoute`, which redirects unauthenticated visitors to `/login` and
sends them on to the page they wanted once they sign in.

### Connecting a Firebase project

1. Create a project at [console.firebase.google.com](https://console.firebase.google.com/).
2. **Build -> Authentication -> Get started -> Sign-in method** -> enable
   **Email/Password**.
3. **Project settings -> General -> Your apps** -> add a **Web app** and copy
   the generated `firebaseConfig` values.
4. `cp .env.example .env` and paste each value into the matching
   `VITE_FIREBASE_*` variable. `.env` is gitignored — no credentials live in
   the source.
5. Restart `npm run dev` (Vite reads env files only at startup).
6. For deployments, add your production domain under
   **Authentication -> Settings -> Authorised domains**.

Until `.env` is filled in the app still boots, and the sign-in screen explains
what is missing instead of crashing.

### Files

| File | Role |
|---|---|
| `src/firebase.js` | Reads `VITE_FIREBASE_*` env vars, initialises the app, exports `auth` |
| `src/auth.js` | `signUp`, `logIn`, `logOut`, `onAuthChange`, `getCurrentUser`, `authErrorMessage` |
| `src/context/AuthContext.jsx` | `AuthProvider` + `useAuth()` -> `{ user, loading }` |
| `src/components/ProtectedRoute.jsx` | Redirects unauthenticated users to `/login` |
| `src/pages/Login.jsx`, `src/pages/SignUp.jsx` | The two auth screens |

Example usage:

```js
import { signUp, logIn, logOut, onAuthChange } from './auth.js'

await signUp('user@acme.com', 'hunter2', 'Reem K')   // create account + sign in
await logIn('user@acme.com', 'hunter2')              // sign in
await logOut()                                       // sign out

const unsubscribe = onAuthChange((user) => { /* null when signed out */ })
```

Inside components, prefer the context:

```jsx
import { useAuth } from './context/AuthContext.jsx'

const { user, loading } = useAuth()
```

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with HMR |
| `npm run build` | Type/lint-free production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Run Oxlint |
