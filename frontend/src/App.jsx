import {
  Bell,
  ChevronRight,
  Files,
  History,
  LayoutGrid,
  LogOut,
  Plus,
  PlusCircle,
  Scale,
  Search,
  Workflow,
  Zap,
} from 'lucide-react'
import { NavLink, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import GovernAILogo from './components/Logo.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'
import { logOut } from './auth.js'
import Login from './pages/Login.jsx'
import SignUp from './pages/SignUp.jsx'
import Overview from './pages/Overview.jsx'
import Reports from './pages/Reports.jsx'
import SubmitUseCase from './pages/SubmitUseCase.jsx'
import PipelineRun from './pages/PipelineRun.jsx'
import ReportDetail from './pages/ReportDetail.jsx'
import Policies from './pages/Policies.jsx'
import AuditLog from './pages/AuditLog.jsx'

import './App.css'

const NAV_MAIN = [
  { to: '/', label: 'Overview', icon: LayoutGrid, end: true },
  { to: '/reports', label: 'Reports', icon: Files },
  { to: '/submit', label: 'Submit use case', icon: PlusCircle },
  { to: '/pipeline-run', label: 'Pipeline runs', icon: Workflow },
]

const NAV_GOV = [
  { to: '/policies', label: 'Policies', icon: Scale },
  { to: '/audit-log', label: 'Audit log', icon: History },
]

const TITLES = {
  '/': 'Overview',
  '/reports': 'Reports',
  '/submit': 'Submit use case',
  '/pipeline-run': 'Pipeline run',
  '/policies': 'Policies',
  '/audit-log': 'Audit log',
}

function pageTitle(pathname) {
  if (TITLES[pathname]) return TITLES[pathname]
  if (pathname.startsWith('/use-cases/')) return 'Report detail'
  return 'GovernAI'
}

function displayNameFor(user) {
  if (!user) return 'Governance Team'
  return user.displayName || user.email?.split('@')[0] || 'Governance Team'
}

function initialsFor(user) {
  const name = displayNameFor(user)
  const parts = name.trim().split(/[\s._-]+/).filter(Boolean)
  const letters = parts.length > 1 ? parts[0][0] + parts[1][0] : name.slice(0, 2)
  return letters.toUpperCase()
}

function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  async function handleSignOut() {
    try {
      await logOut()
    } finally {
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="sidebar-brand">
          <GovernAILogo size={26} gradientId="sidebar-logo" />
          <span className="sidebar-brand-text">
            Govern<span className="brand-ai">AI</span>
          </span>
        </NavLink>

        <div className="nav-group-label">Workspace</div>
        <nav className="sidebar-nav">
          {NAV_MAIN.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
            >
              <item.icon size={16} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="nav-group-label">Governance</div>
        <nav className="sidebar-nav">
          {NAV_GOV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
            >
              <item.icon size={16} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-spacer" />

        <div className="agents-online-card">
          <div className="agents-online-head">
            <Zap size={13} className="tone-teal" />
            Agents online
          </div>
          <div className="agents-online-note">3 / 3 healthy · gpt-4o-mini via OpenAI</div>
        </div>

        <div className="sidebar-user-row">
          <div className="sidebar-avatar">{initialsFor(user)}</div>
          <div className="sidebar-user-text">
            <div className="sidebar-user-name">{displayNameFor(user)}</div>
            <div className="sidebar-user-role">GRC Lead</div>
          </div>
          <LogOut size={15} className="sidebar-signout" onClick={handleSignOut} />
        </div>
      </aside>

      <div className="main-col">
        <header className="topbar">
          <div className="breadcrumb">
            <span>GovernAI</span>
            <ChevronRight size={11} />
            <span className="breadcrumb-current">{pageTitle(location.pathname)}</span>
          </div>
          <div className="topbar-spacer" />
          <div className="topbar-search">
            <Search size={14} />
            <span>Search use cases, policies…</span>
            <span className="topbar-kbd">⌘K</span>
          </div>
          <div className="topbar-bell">
            <Bell size={15} />
            <span className="topbar-bell-dot" />
          </div>
          <button className="topbar-cta" onClick={() => navigate('/submit')}>
            <Plus size={14} />
            New use case
          </button>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

/** Keeps signed-in users off the auth screens. */
function PublicOnlyRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) return <div className="loading">Checking your session…</div>
  if (user) return <Navigate to="/" replace />
  return children
}

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicOnlyRoute>
            <SignUp />
          </PublicOnlyRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Overview />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/submit" element={<SubmitUseCase />} />
        <Route path="/pipeline-run" element={<PipelineRun />} />
        <Route path="/policies" element={<Policies />} />
        <Route path="/audit-log" element={<AuditLog />} />
        <Route path="/use-cases/:id" element={<ReportDetail />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
