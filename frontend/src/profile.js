// Job levels offered at sign-up. Values must match app/users.py JobLevel.
export const JOB_LEVELS = [
  { value: 'entry', label: 'Entry level' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead / Principal' },
  { value: 'manager', label: 'Manager' },
  { value: 'director', label: 'Director' },
  { value: 'executive', label: 'Executive (VP / C-level)' },
]

export function jobLevelLabel(value) {
  return JOB_LEVELS.find((level) => level.value === value)?.label || ''
}

// Mirrors USERNAME_PATTERN in app/users.py so the form can fail fast.
export const USERNAME_PATTERN = /^[A-Za-z0-9_.]{3,30}$/

export function validateProfile({ username, jobLevel }) {
  if (!USERNAME_PATTERN.test(username.trim())) {
    return "Username must be 3–30 characters: letters, digits, '_' or '.'"
  }
  if (!jobLevel) return 'Choose your job level.'
  return ''
}

// Firebase signs a new account in (and App starts loading its profile) before
// the sign-up form has saved that profile. App waits on this so it doesn't
// briefly see "no profile" for a brand-new user.
let signUpInFlight = null

export function trackSignUp(promise) {
  signUpInFlight = promise
  promise.catch(() => {}).finally(() => {
    if (signUpInFlight === promise) signUpInFlight = null
  })
  return promise
}

/** Waits for a pending sign-up; resolves to its error (if it failed) or null. */
export async function waitForSignUp() {
  if (!signUpInFlight) return null
  try {
    await signUpInFlight
    return null
  } catch (err) {
    return err
  }
}
