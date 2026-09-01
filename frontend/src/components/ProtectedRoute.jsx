import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext.jsx'

/**
 * Gates the dashboard. While Firebase restores the session we render a neutral
 * loading state; unauthenticated visitors are sent to /login and returned to
 * the page they wanted after signing in.
 */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div className="loading">Checking your session…</div>
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return children
}
