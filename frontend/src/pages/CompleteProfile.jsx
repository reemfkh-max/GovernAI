import { useState } from 'react'

import GovernAILogo from '../components/Logo.jsx'
import ProfileFields from '../components/ProfileFields.jsx'
import { saveMyProfile } from '../api.js'
import { validateProfile } from '../profile.js'

// Shown to a signed-in user who has no profile yet — e.g. after Google
// sign-in, or when the username picked at sign-up was already taken.
export default function CompleteProfile({ user, initialError, onSaved, onSignOut }) {
  const [username, setUsername] = useState(user?.displayName?.replace(/\s+/g, '') || '')
  const [jobLevel, setJobLevel] = useState('')
  const [error, setError] = useState(initialError || '')
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()

    const invalid = validateProfile({ username, jobLevel })
    if (invalid) {
      setError(invalid)
      return
    }

    setBusy(true)
    setError('')
    try {
      onSaved(await saveMyProfile({ username: username.trim(), jobLevel }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="login-hero-top">
          <GovernAILogo size={34} gradientId="profile-logo" />
          <span className="login-hero-brand">
            Govern<span className="brand-ai">AI</span>
          </span>
        </div>
      </div>

      <div className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <h2>Complete your profile</h2>
          <p className="login-form-sub">Signed in as {user?.email}</p>

          <ProfileFields
            username={username}
            jobLevel={jobLevel}
            onUsername={setUsername}
            onJobLevel={setJobLevel}
          />

          {error && <div className="login-error">{error}</div>}

          <button className="login-submit" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : 'Continue'}
          </button>

          <button className="login-switch" type="button" onClick={onSignOut}>
            Sign out
          </button>
        </form>
      </div>
    </div>
  )
}
