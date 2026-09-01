/**
 * The "or continue with" block shared by the Login and Sign up screens.
 * Uses the existing `.login-divider` / `.login-sso` styles — the only new rule
 * is the spacing between the two stacked buttons.
 */

function GoogleMark({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" focusable="false">
      <path
        fill="#4285f4"
        d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"
      />
      <path
        fill="#34a853"
        d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"
      />
      <path
        fill="#fbbc05"
        d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34A21.99 21.99 0 0 0 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"
      />
      <path
        fill="#ea4335"
        d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"
      />
    </svg>
  )
}

function MicrosoftMark({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 23 23" aria-hidden="true" focusable="false">
      <path fill="#f25022" d="M1 1h10v10H1z" />
      <path fill="#7fba00" d="M12 1h10v10H12z" />
      <path fill="#00a4ef" d="M1 12h10v10H1z" />
      <path fill="#ffb900" d="M12 12h10v10H12z" />
    </svg>
  )
}

const PROVIDERS = [
  { id: 'google', label: 'Continue with Google', Mark: GoogleMark },
  { id: 'microsoft', label: 'Continue with Microsoft', Mark: MicrosoftMark },
]

export default function SsoButtons({ busy = false, pending = null, onSelect }) {
  return (
    <>
      <div className="login-divider">
        <span />
        <em>or</em>
        <span />
      </div>

      {PROVIDERS.map(({ id, label, Mark }) => (
        <button
          key={id}
          className="login-sso"
          type="button"
          disabled={busy}
          onClick={() => onSelect(id)}
        >
          <Mark />
          {pending === id ? 'Opening…' : label}
        </button>
      ))}
    </>
  )
}
