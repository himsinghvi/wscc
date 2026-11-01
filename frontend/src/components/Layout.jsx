import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import InstallPrompt from './InstallPrompt'
import Footer from './Footer'

// `cap` gates an item to a persona capability; omit = visible to everyone.
const SECTIONS = [
  {
    title: 'Weekend',
    items: [
      { to: '/', icon: 'grid-1x2-fill', label: 'Dashboard' },
      { to: '/availability', icon: 'calendar-check-fill', label: 'Availability', cap: 'availability.submit' },
      { to: '/rankings', icon: 'bar-chart-steps', label: 'Rankings' },
      { to: '/backout', icon: 'box-arrow-left', label: 'Backout', cap: 'availability.submit' },
      { to: '/scheduler', icon: 'cpu-fill', label: 'AI Scheduler', cap: 'schedule.manage' },
    ],
  },
  {
    title: 'Explore',
    items: [
      { to: '/matches', icon: 'calendar-week-fill', label: 'Schedule & Matches' },
      { to: '/teams', icon: 'people-fill', label: 'Teams' },
      { to: '/grounds', icon: 'geo-alt-fill', label: 'Grounds' },
      { to: '/stats', icon: 'graph-up-arrow', label: 'Stats' },
      { to: '/tournaments', icon: 'award-fill', label: 'Tournaments' },
      { to: '/directory', icon: 'telephone-fill', label: 'Directory' },
    ],
  },
]

function NavItem({ item, onNavigate }) {
  return (
    <NavLink to={item.to} end={item.to === '/'} onClick={onNavigate}
      className={({ isActive }) => 'wscc-nav-link' + (isActive ? ' active' : '')}>
      {({ isActive }) => (
        <>
          {isActive && <motion.span layoutId="nav-pill" className="nav-active-pill"
            transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
          <i className={`bi bi-${item.icon}`} />
          <span>{item.label}</span>
        </>
      )}
    </NavLink>
  )
}

function SidebarInner({ me, onNavigate }) {
  const caps = new Set(me?.capabilities || [])
  const allowed = (it) => !it.cap || caps.has(it.cap)
  const sections = SECTIONS
    .map((s) => ({ ...s, items: s.items.filter(allowed) }))
    .filter((s) => s.items.length)
  const manage = [
    { to: '/poll-schedule', icon: 'calendar-event-fill', label: 'Poll Schedule', cap: 'poll.manage' },
    { to: '/day-rules', icon: 'calendar-x-fill', label: 'Availability rules', cap: 'rules.manage' },
    { to: '/admin', icon: 'sliders', label: 'Admin', cap: 'admin.config' },
  ].filter(allowed)
  if (manage.length) sections.push({ title: 'Manage', items: manage })

  return (
    <div className="d-flex flex-column h-100 p-3">
      <div className="d-flex align-items-center gap-2 mb-4 px-1">
        <div className="brand-badge d-grid" style={{ placeItems: 'center' }}>
          <i className="bi bi-lightning-charge-fill text-white" />
        </div>
        <div>
          <div className="fw-bold lh-1 gradient-text" style={{ fontSize: '1.05rem' }}>WSCC</div>
          <div className="text-muted-2" style={{ fontSize: '.68rem' }}>Weekend Cricket League</div>
        </div>
      </div>

      <nav className="flex-grow-1 overflow-auto pe-1">
        {sections.map((s) => (
          <div key={s.title} className="mb-3">
            <div className="text-muted-2 text-uppercase px-2 mb-1" style={{ fontSize: '.64rem', letterSpacing: '.12em' }}>{s.title}</div>
            {s.items.map((it) => <NavItem key={it.to} item={it} onNavigate={onNavigate} />)}
          </div>
        ))}
      </nav>

      <InstallPrompt />
    </div>
  )
}

export default function Layout({ children }) {
  const { me, signOut } = useAuth()
  const [drawer, setDrawer] = useState(false)
  const location = useLocation()
  useEffect(() => { setDrawer(false) }, [location.pathname])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
  const name = me?.email?.split('@')[0]

  return (
    <div className="d-flex">
      {/* Desktop sidebar */}
      <aside className="wscc-sidebar d-none d-lg-block">
        <SidebarInner me={me} />
      </aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {drawer && (
          <>
            <motion.div className="position-fixed top-0 start-0 w-100 h-100" style={{ background: 'rgba(3,6,15,.6)', zIndex: 1040 }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setDrawer(false)} />
            <motion.aside className="wscc-sidebar position-fixed top-0 start-0" style={{ zIndex: 1050 }}
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 360, damping: 34 }}>
              <SidebarInner me={me} onNavigate={() => setDrawer(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex-grow-1" style={{ minWidth: 0 }}>
        <header className="wscc-topbar d-flex align-items-center justify-content-between px-3 py-2">
          <div className="d-flex align-items-center gap-2">
            <button className="btn btn-sm btn-outline-light d-lg-none" onClick={() => setDrawer(true)}>
              <i className="bi bi-list" />
            </button>
            <div className="d-none d-sm-block">
              <div className="small text-muted-2 lh-1">{greeting},</div>
              <div className="fw-semibold text-capitalize lh-1">{name}</div>
            </div>
          </div>

          <div className="d-flex align-items-center gap-2">
            <span className="pill pill-wait d-none d-md-inline-flex text-capitalize">
              <i className="bi bi-shield-lock-fill" /> {me?.role}
            </span>
            <span className="d-lg-none"><InstallPrompt compact /></span>
            <motion.button className="btn btn-sm btn-outline-light" onClick={signOut}
              whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.95 }}>
              <i className="bi bi-box-arrow-right" /> <span className="d-none d-sm-inline">Sign out</span>
            </motion.button>
          </div>
        </header>

        <main className="p-3 p-md-4" style={{ maxWidth: 1280, margin: '0 auto' }}>
          {children}
          <Footer />
        </main>
      </div>
    </div>
  )
}
