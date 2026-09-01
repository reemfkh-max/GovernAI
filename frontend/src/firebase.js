// Firebase app + auth initialisation.
//
// Config comes from Vite env vars (frontend/.env.local — see .env.example).
// Copy the values from the Firebase console:
//   Project settings → General → Your apps → Web app → SDK setup and config.
//
// When the config is missing the app stays in "demo mode": the sign-in screen
// still works (local flag only) so the UI can be run without a Firebase
// project, exactly as it did before Firebase was wired in.
import { initializeApp } from 'firebase/app'
import { browserLocalPersistence, getAuth, setPersistence } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

export const firebaseEnabled = Boolean(
  firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.appId
)

let app = null
let auth = null

if (firebaseEnabled) {
  app = initializeApp(firebaseConfig)
  auth = getAuth(app)
  // Keep the session across reloads/tabs.
  setPersistence(auth, browserLocalPersistence).catch((error) => {
    console.warn('Firebase auth persistence unavailable:', error)
  })
}

export { app, auth }
