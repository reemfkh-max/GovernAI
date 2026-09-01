import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { onAuthChange } from '../auth.js'

const AuthContext = createContext({ user: null, loading: true })

/**
 * Watches Firebase auth state once for the whole app so components can read
 * `{ user, loading }` without each subscribing separately.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthChange((nextUser) => {
      setUser(nextUser)
      setLoading(false)
    })
    return unsubscribe
  }, [])

  const value = useMemo(() => ({ user, loading }), [user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/** `{ user, loading }` — `loading` is true until the session is restored. */
export function useAuth() {
  return useContext(AuthContext)
}
