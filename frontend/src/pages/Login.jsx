import { useState } from 'react'
import { Building2 } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import AuthHero from '../components/AuthHero.jsx'
import { authErrorMessage, isFirebaseConfigured, logIn } from '../auth.js'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

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

          <div className="login-divider">
            <span />
            <em>or</em>
            <span />
          </div>

          <button
            className="login-sso"
            type="button"
            onClick={() => setError('SSO is not enabled yet — sign in with your work email and password.')}
          >
            <Building2 size={15} />
            Continue with SSO
          </button>

          <p className="login-alt">
            No account yet? <Link to="/signup">Create one</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
