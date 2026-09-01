import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import AuthHero from '../components/AuthHero.jsx'
import SsoButtons from '../components/SsoButtons.jsx'
import {
  authErrorMessage,
  isFirebaseConfigured,
  isPopupDismissed,
  logIn,
  signInWithProvider,
} from '../auth.js'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [ssoPending, setSsoPending] = useState(null)

  // Where the user was headed before ProtectedRoute bounced them here.
  const redirectTo = location.state?.from?.pathname || '/'

  async function submit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)

    try {
      await logIn(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(authErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function signInWithSso(providerId) {
    setError(null)
    setBusy(true)
    setSsoPending(providerId)

    try {
      await signInWithProvider(providerId)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      // Closing the provider pop-up is a cancellation, not an error.
      if (!isPopupDismissed(err)) setError(authErrorMessage(err))
    } finally {
      setBusy(false)
      setSsoPending(null)
    }
  }

  return (
    <div className="login-page">
      <AuthHero gradientId="login-logo" />

      <div className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <h2>Sign in</h2>
          <p className="login-form-sub">Governance, risk &amp; compliance workspace</p>

          {!isFirebaseConfigured && (
            <div className="error-banner">
              Firebase is not configured yet. Copy <code>frontend/.env.example</code> to{' '}
              <code>frontend/.env</code>, add your <code>VITE_FIREBASE_*</code> values and
              restart the dev server.
            </div>
          )}

          {error && <div className="error-banner">{error}</div>}

          <div className="field">
            <label htmlFor="login-email">Work email</label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <button className="login-submit" type="submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>

          <SsoButtons busy={busy} pending={ssoPending} onSelect={signInWithSso} />

          <p className="login-alt">
            {/* Carry the intended destination across to sign up. */}
            No account yet? <Link to="/signup" state={location.state}>Create one</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
