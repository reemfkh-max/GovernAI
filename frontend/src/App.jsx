import { useEffect, useState } from 'react'
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
import { NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import GovernAILogo from './components/Logo.jsx'
import { firebaseEnabled, signOut, watchAuth } from './auth.js'
import { getMyProfile } from './api.js'
import { jobLevelLabel, waitForSignUp } from './profile.js'
import CompleteProfile from './pages/CompleteProfile.jsx'
import Login from './pages/Login.jsx'
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

function userLabel(user, profile) {
  return profile?.username || user?.displayName || user?.email || 'Governance Team'
}

function userInitials(user, profile) {
  const source = profile?.username || user?.displayName || user?.email || 'Governance AI'
  const parts = source.replace(/@.*$/, '').split(/[\s._-]+/).filter(Boolean)
  const initials = parts.slice(0, 2).map((part) => part[0]).join('')
  return (initials || 'GA').toUpperCase()
}


function AppShell({ user, profile, onSignOut }) {
  const navigate = useNavigate()
  const location = useLocation()

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
          <div className="sidebar-avatar">{userInitials(user, profile)}</div>
          <div className="sidebar-user-text">
            <div className="sidebar-user-name">{userLabel(user, profile)}</div>
            <div className="sidebar-user-role">
              {jobLevelLabel(profile?.job_level) || 'GRC Lead'}
            </div>
          </div>
          <LogOut size={15} className="sidebar-signout" onClick={onSignOut} />
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
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/submit" element={<SubmitUseCase />} />
            <Route path="/pipeline-run" element={<PipelineRun />} />
            <Route path="/policies" element={<Policies />} />
            <Route path="/audit-log" element={<AuditLog />} />
            <Route path="/use-cases/:id" element={<ReportDetail />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function App() {
  // null = signed out, undefined = still resolving the Firebase session.
  const [user, setUser] = useState(undefined)

  // The profile loaded for a given uid. `value` is null when that user has
  // not saved a profile yet, false when the backend could not be reached.
  const [loadedProfile, setLoadedProfile] = useState({ uid: null, value: null, error: '' })

  useEffect(() => watchAuth(setUser), [])

  const uid = user?.uid
  const needsProfile = Boolean(uid) && firebaseEnabled

  useEffect(() => {
    if (!needsProfile) return

    let cancelled = false

    ;(async () => {
      const signUpError = await waitForSignUp()
      let value
      try {
        value = await getMyProfile()
      } catch (err) {
        // Backend unreachable — let them in with the fallback sidebar label.
        console.warn('Could not load profile:', err)
        value = false
      }
      if (!cancelled) {
        setLoadedProfile({ uid, value, error: signUpError?.message || '' })
      }
    })()

    return () => {
      cancelled = true
    }
  }, [uid, needsProfile])

  // undefined = still loading, null = no profile saved yet.
  let profile = null
  if (needsProfile) {
    profile = loadedProfile.uid === uid ? loadedProfile.value : undefined
  }

  const handleSignOut = () => signOut().then(() => setUser(null))

  if (user === undefined || (user && profile === undefined)) {
    return <div className="app-booting">Loading…</div>
  }

  if (user === null) {
    // In demo mode watchAuth has no listener, so Login reports success itself.
    return <Login onSignedIn={() => setUser((current) => current ?? { uid: 'demo-user' })} />
  }

  if (firebaseEnabled && profile === null) {
    return (
      <CompleteProfile
        user={user}
        initialError={loadedProfile.error}
        onSaved={(value) => setLoadedProfile({ uid, value, error: '' })}
        onSignOut={handleSignOut}
      />
    )
  }

  return <AppShell user={user} profile={profile || null} onSignOut={handleSignOut} />
}

export default App
