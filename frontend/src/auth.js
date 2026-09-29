// Authentication layer.
//
// With Firebase configured (see firebase.js) this is real Firebase
// Authentication: email/password + Google sign-in, a persisted session, and
// an ID token that api.js attaches to every backend request.
//
// Without Firebase config the module falls back to the previous demo
// behaviour — a local flag that gates the sign-in screen — so the UI can be
// run and reviewed without a Firebase project.
import {
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  updateProfile,
} from 'firebase/auth'

import { auth, firebaseEnabled } from './firebase.js'

export { firebaseEnabled }

// Demo-mode session flag (unused when Firebase is configured).
export const SIGNED_IN_KEY = 'governai_signed_in'

/** Subscribe to auth-state changes. Returns an unsubscribe function. */
export function watchAuth(callback) {
  if (!firebaseEnabled) {
    callback(
      localStorage.getItem(SIGNED_IN_KEY) === '1'
        ? { uid: 'demo-user', email: 'demo@governai.local', displayName: 'Demo User' }
        : null
    )
    return () => {}
  }

  return onAuthStateChanged(auth, (user) => {
    callback(
      user
        ? {
            uid: user.uid,
            email: user.email,
            displayName: user.displayName,
            emailVerified: user.emailVerified,
          }
        : null
    )
  })
}

export async function signInWithEmail(email, password) {
  if (!firebaseEnabled) {
    localStorage.setItem(SIGNED_IN_KEY, '1')
    return
  }
  await signInWithEmailAndPassword(auth, email, password)
}

export async function registerWithEmail(email, password, displayName) {
  if (!firebaseEnabled) {
    localStorage.setItem(SIGNED_IN_KEY, '1')
    return
  }
  const credential = await createUserWithEmailAndPassword(auth, email, password)
  if (displayName) {
    await updateProfile(credential.user, { displayName })
  }
}

export async function signInWithGoogle() {
  if (!firebaseEnabled) {
    localStorage.setItem(SIGNED_IN_KEY, '1')
    return
  }
  await signInWithPopup(auth, new GoogleAuthProvider())
}

export async function signOut() {
  localStorage.removeItem(SIGNED_IN_KEY)
  if (firebaseEnabled) {
    await firebaseSignOut(auth)
  }
}

/** Current Firebase ID token, or null in demo mode / when signed out. */
export async function getIdToken() {
  if (!firebaseEnabled) return null
  const user = auth.currentUser
  if (!user) return null
  return user.getIdToken()
}

/** Turn a Firebase auth error into something worth showing a user. */
export function authErrorMessage(error) {
  const code = error?.code || ''

  switch (code) {
    case 'auth/invalid-email':
      return 'That email address is not valid.'
    case 'auth/missing-password':
      return 'Enter your password.'
    case 'auth/weak-password':
      return 'Password must be at least 6 characters.'
    case 'auth/email-already-in-use':
      return 'An account already exists for this email — sign in instead.'
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'Incorrect email or password.'
    case 'auth/too-many-requests':
      return 'Too many attempts. Try again in a few minutes.'
    case 'auth/popup-closed-by-user':
      return 'Sign-in window was closed before finishing.'
    case 'auth/operation-not-allowed':
      return 'This sign-in method is disabled in the Firebase console.'
    default:
      return error?.message || 'Sign-in failed. Please try again.'
  }
}
