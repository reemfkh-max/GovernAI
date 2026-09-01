// Firebase bootstrap for the GovernAI frontend.
//
// Credentials are never hard-coded — they come from Vite environment variables
// (see `.env.example`). Vite only exposes variables prefixed with `VITE_`, and
// they are inlined at build time, so this file needs no runtime secrets.
import { initializeApp, getApp, getApps } from 'firebase/app'
import { connectAuthEmulator, getAuth } from 'firebase/auth'

export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

// The two keys the Auth SDK actually needs to talk to a project. When they are
// missing we skip initialisation instead of throwing, so the app still boots
// and the sign-in screens can explain what to configure.
export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId,
)

export const FIREBASE_NOT_CONFIGURED_MESSAGE =
  'Firebase is not configured. Copy frontend/.env.example to frontend/.env, ' +
  'fill in your VITE_FIREBASE_* values, then restart the dev server.'

// `getApps()` guard keeps Vite HMR from re-initialising the app on every reload.
export const firebaseApp = isFirebaseConfigured
  ? getApps().length
    ? getApp()
    : initializeApp(firebaseConfig)
  : null

export const auth = firebaseApp ? getAuth(firebaseApp) : null

// Optional: point the SDK at a local Firebase Auth emulator for development
// (`VITE_FIREBASE_AUTH_EMULATOR_HOST=http://127.0.0.1:9099`). Unset in
// production — the app then talks to the real project.
const emulatorHost = import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST
if (auth && emulatorHost) {
  connectAuthEmulator(auth, emulatorHost, { disableWarnings: true })
}
