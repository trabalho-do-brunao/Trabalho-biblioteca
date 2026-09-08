import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './AuthContext'

export default function ProtectedRoute() {
  const location = useLocation()
  const { authenticated, loading } = useAuth()

  if (loading) {
    return (
      <main className="auth-loading" aria-live="polite">
        Verificando acesso...
      </main>
    )
  }

  if (!authenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
