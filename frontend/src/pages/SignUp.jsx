import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import AuthHero from '../components/AuthHero.jsx'
import { authErrorMessage, isFirebaseConfigured, signUp } from '../auth.js'

export default function SignUp() {
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError(null)

    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setBusy(true)
    try {
      // Firebase signs the new account in immediately, so go straight to the
      // dashboard — ProtectedRoute will already see the session.
      await signUp(email, password, name)
      navigate('/', { replace: true })
    } catch (err) {
      setError(authErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <AuthHero gradientId="signup-logo" />

      <div className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <h2>Create account</h2>
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
            <label htmlFor="signup-name">Full name</label>
            <input
              id="signup-name"
              autoComplete="name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="signup-email">Work email</label>
            <input
              id="signup-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <div className="hint">At least 6 characters.</div>
          </div>

          <div className="field">
            <label htmlFor="signup-confirm">Confirm password</label>
            <input
              id="signup-confirm"
              type="password"
              autoComplete="new-password"
              required
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
            />
          </div>

          <button className="login-submit" type="submit" disabled={busy}>
            {busy ? 'Creating account…' : 'Create account'}
          </button>

          <p className="login-alt">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
