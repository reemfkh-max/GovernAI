import { useState } from 'react'
import { Building2, Gavel, Scale, ShieldCheck } from 'lucide-react'

import GovernAILogo from '../components/Logo.jsx'
import {
  authErrorMessage,
  firebaseEnabled,
  registerWithEmail,
  signInWithEmail,
  signInWithGoogle,
} from '../auth.js'

export default function Login({ onSignedIn }) {
  const [email, setEmail] = useState(firebaseEnabled ? '' : 'lujain@acme.com')
  const [password, setPassword] = useState(firebaseEnabled ? '' : 'governai')
  const [mode, setMode] = useState('signin') // 'signin' | 'signup'
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // Runs the given Firebase call, surfacing errors on the form.
  async function run(action) {
    setBusy(true)
    setError('')

    try {
      await action()
      onSignedIn?.()
    } catch (err) {
      setError(authErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function submitForm(event) {
    event?.preventDefault()
    run(() =>
      mode === 'signup'
        ? registerWithEmail(email, password)
        : signInWithEmail(email, password)
    )
  }

  function continueWithGoogle() {
    run(signInWithGoogle)
  }

  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="login-hero-top">
          <GovernAILogo size={34} gradientId="login-logo" />
          <span className="login-hero-brand">
            Govern<span className="brand-ai">AI</span>
          </span>
        </div>

        <div className="login-hero-mid">
          <div className="login-hero-kicker">Multi-agent governance</div>
          <h1 className="login-hero-title">
            Every AI use case reviewed before it ships.
          </h1>
          <p className="login-hero-sub">
            Risk assessment, policy compliance and a decision — three agents,
            real tools, an append-only audit trail.
          </p>

          <div className="login-hero-pills">
            <span className="login-pill login-pill-teal">
              <ShieldCheck size={13} />
              Risk agent
            </span>
            <span className="login-pill login-pill-violet">
              <Scale size={13} />
              Policy agent
            </span>
            <span className="login-pill login-pill-neutral">
              <Gavel size={13} />
              Decision agent
            </span>
          </div>
        </div>

        <div className="login-hero-foot">
          POL-001 – POL-140 · audit_log.jsonl · OpenAI
        </div>
      </div>

      <div className="login-panel">
        <form className="login-form" onSubmit={submitForm}>
          <h2>{mode === 'signup' ? 'Create account' : 'Sign in'}</h2>
          <p className="login-form-sub">Governance, risk &amp; compliance workspace</p>

          <div className="field">
            <label htmlFor="login-email">Work email</label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button className="login-submit" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'signup' ? 'Create account' : 'Sign in'}
          </button>

          {firebaseEnabled && (
            <button
              className="login-switch"
              type="button"
              onClick={() => {
                setMode(mode === 'signup' ? 'signin' : 'signup')
                setError('')
              }}
            >
              {mode === 'signup'
                ? 'Already have an account? Sign in'
                : 'New here? Create an account'}
            </button>
          )}

          <div className="login-divider">
            <span />
            <em>or</em>
            <span />
          </div>

          <button
            className="login-sso"
            type="button"
            onClick={continueWithGoogle}
            disabled={busy}
          >
            <Building2 size={15} />
            Continue with Google
          </button>

          {!firebaseEnabled && (
            <p className="login-demo-note">
              Demo mode — Firebase is not configured, so any credentials get you
              in. Add the VITE_FIREBASE_* variables in frontend/.env.local to
              enable real sign-in.
            </p>
          )}
        </form>
      </div>
    </div>
  )
}
