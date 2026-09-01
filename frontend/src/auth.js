// Reusable authentication helpers built on the Firebase modular SDK.
//
// Every export here is a thin, UI-agnostic wrapper so pages/components never
// import `firebase/auth` directly.
import {
  GoogleAuthProvider,
  OAuthProvider,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  updateProfile,
} from 'firebase/auth'

import { auth, isFirebaseConfigured, FIREBASE_NOT_CONFIGURED_MESSAGE } from './firebase.js'

/** Human-readable messages for the Firebase Auth error codes we can hit. */
const ERROR_MESSAGES = {
  'auth/invalid-email': 'That email address is not valid.',
  'auth/missing-password': 'Please enter a password.',
  'auth/weak-password': 'Password must be at least 6 characters.',
  'auth/email-already-in-use': 'An account with this email already exists.',
  'auth/user-not-found': 'No account found for this email.',
  'auth/wrong-password': 'Incorrect email or password.',
  'auth/invalid-credential': 'Incorrect email or password.',
  'auth/too-many-requests': 'Too many attempts. Try again in a few minutes.',
  'auth/network-request-failed': 'Network error — check your connection and try again.',
  'auth/operation-not-allowed':
    'This sign-in method is disabled for this Firebase project. Enable it under Authentication → Sign-in method.',
  'auth/popup-blocked':
    'Your browser blocked the sign-in window. Allow pop-ups for this site and try again.',
  'auth/unauthorized-domain':
    'This domain is not authorised for sign-in. Add it under Authentication → Settings → Authorised domains.',
  'auth/account-exists-with-different-credential':
    'An account already exists with this email. Sign in with the method you used originally.',
}

/** Error codes that just mean "the user closed the pop-up" — not worth showing. */
const DISMISSED_POPUP_CODES = new Set([
  'auth/popup-closed-by-user',
  'auth/cancelled-popup-request',
  'auth/user-cancelled',
])

/** True when the user simply dismissed the SSO pop-up; callers can stay silent. */
export function isPopupDismissed(error) {
  return DISMISSED_POPUP_CODES.has(error?.code)
}

/** Turns a Firebase error (or anything else) into a message safe to render. */
export function authErrorMessage(error) {
  if (!error) return 'Something went wrong. Please try again.'
  return ERROR_MESSAGES[error.code] || error.message || 'Something went wrong. Please try again.'
}

function requireAuth() {
  if (!isFirebaseConfigured || !auth) {
    const error = new Error(FIREBASE_NOT_CONFIGURED_MESSAGE)
    error.code = 'governai/firebase-not-configured'
    throw error
  }
  return auth
}

/**
 * Create an account with email + password.
 * `displayName` is optional and stored on the Firebase user profile.
 * Resolves with the signed-in `User` (Firebase signs new users in immediately).
 */
export async function signUp(email, password, displayName) {
  const instance = requireAuth()
  const credential = await createUserWithEmailAndPassword(
    instance,
    email.trim(),
    password,
  )

  if (displayName?.trim()) {
    await updateProfile(credential.user, { displayName: displayName.trim() })
  }

  return credential.user
}

/** Sign in an existing user. Resolves with the `User`. */
export async function logIn(email, password) {
  const instance = requireAuth()
  const credential = await signInWithEmailAndPassword(instance, email.trim(), password)
  return credential.user
}

/** Sign the current user out. */
export async function logOut() {
  const instance = requireAuth()
  await firebaseSignOut(instance)
}

/**
 * Subscribe to authentication state.
 * Calls `callback(user | null)` immediately with the restored session and again
 * on every change. Returns an unsubscribe function.
 */
export function onAuthChange(callback) {
  if (!isFirebaseConfigured || !auth) {
    // Nothing to observe — report "signed out" once so callers stop loading.
    callback(null)
    return () => {}
  }
  return onAuthStateChanged(auth, callback)
}

/**
 * The currently signed-in user, or `null`.
 * Note: this is `null` until Firebase finishes restoring the session on page
 * load — prefer `onAuthChange` / `useAuth()` for rendering decisions.
 */
export function getCurrentUser() {
  return auth?.currentUser ?? null
}

/* =========================================================
   SINGLE SIGN-ON (pop-up based)
========================================================= */

/** The SSO providers wired into the sign-in screens. */
export const SSO_PROVIDERS = {
  google: 'Google',
  microsoft: 'Microsoft',
}

function providerFor(providerId) {
  if (providerId === 'google') {
    const provider = new GoogleAuthProvider()
    provider.setCustomParameters({ prompt: 'select_account' })
    return provider
  }

  if (providerId === 'microsoft') {
    // Azure AD / Microsoft accounts are an OIDC provider in Firebase.
    const provider = new OAuthProvider('microsoft.com')
    provider.setCustomParameters({ prompt: 'select_account' })
    return provider
  }

  throw new Error(`Unknown SSO provider: ${providerId}`)
}

/**
 * Sign in with an SSO provider — `'google'` or `'microsoft'`.
 * Opens the provider's pop-up and resolves with the signed-in `User`.
 * Throws on failure; use `isPopupDismissed(error)` to ignore cancellations.
 */
export async function signInWithProvider(providerId) {
  const instance = requireAuth()
  const credential = await signInWithPopup(instance, providerFor(providerId))
  return credential.user
}

/** Convenience wrappers around `signInWithProvider`. */
export function signInWithGoogle() {
  return signInWithProvider('google')
}

export function signInWithMicrosoft() {
  return signInWithProvider('microsoft')
}

export { isFirebaseConfigured, FIREBASE_NOT_CONFIGURED_MESSAGE }
