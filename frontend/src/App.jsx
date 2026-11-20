import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from './auth/AuthContext'
import Aurora from './components/Aurora'
import Layout from './components/Layout'
import Login from './pages/Login'
import ResetPassword from './pages/ResetPassword'
import Dashboard from './pages/Dashboard'
import Availability from './pages/Availability'
import Rankings from './pages/Rankings'
import Backout from './pages/Backout'
import Teams from './pages/Teams'
import TeamDetail from './pages/TeamDetail'
import Grounds from './pages/Grounds'
import GroundDetail from './pages/GroundDetail'
import Matches from './pages/Matches'
import Stats from './pages/Stats'
import Tournaments from './pages/Tournaments'
import Scheduler from './pages/Scheduler'
import Directory from './pages/Directory'
import CompleteSignup from './pages/CompleteSignup'
import Pending from './pages/Pending'
import Approvals from './pages/Approvals'
import Members from './pages/Members'
import DayRules from './pages/DayRules'
import PollSchedule from './pages/PollSchedule'
import Admin from './pages/Admin'

export default function App() {
  const { me, loading } = useAuth()
  const location = useLocation()
  const can = (c) => me?.capabilities?.includes(c)

  if (loading) {
    return (
      <>
        <Aurora />
        <div className="d-flex vh-100 align-items-center justify-content-center">
          <div className="brand-badge" style={{ width: 54, height: 54 }} />
        </div>
      </>
    )
  }

  // password-reset landing (from the email link) — available regardless of auth state
  if (location.pathname === '/reset') return (<><Aurora /><ResetPassword /></>)

  if (!me) return (<><Aurora /><Login /></>)
  if (me.status === 'unregistered') return (<><Aurora /><CompleteSignup /></>)
  if (me.status && me.status !== 'ok') return (<><Aurora /><Pending /></>)

  return (
    <>
      <Aurora />
      <Layout>
        {/* Enter-only keyed transition: the previous page unmounts immediately on
            route change (no AnimatePresence exit node left on top), so taps never
            get swallowed by a stuck overlay on mobile. */}
        <motion.div key={location.pathname} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, ease: [0.22, 0.61, 0.36, 1] }}>
            <Routes location={location}>
              <Route path="/" element={<Dashboard />} />
              {can('availability.submit') && <Route path="/availability" element={<Availability />} />}
              <Route path="/rankings" element={<Rankings />} />
              {can('availability.submit') && <Route path="/backout" element={<Backout />} />}
              <Route path="/teams" element={<Teams />} />
              <Route path="/teams/:id" element={<TeamDetail />} />
              <Route path="/grounds" element={<Grounds />} />
              <Route path="/grounds/:id" element={<GroundDetail />} />
              <Route path="/matches" element={<Matches />} />
              <Route path="/stats" element={<Stats />} />
              <Route path="/tournaments" element={<Tournaments />} />
              {can('schedule.manage') && <Route path="/scheduler" element={<Scheduler />} />}
              <Route path="/directory" element={<Directory />} />
              {can('signup.approve') && <Route path="/approvals" element={<Approvals />} />}
              {can('admin.config') && <Route path="/members" element={<Members />} />}
              {me.is_admin && <Route path="/poll-schedule" element={<PollSchedule />} />}
              {me.is_admin && <Route path="/day-rules" element={<DayRules />} />}
              {me.is_admin && <Route path="/admin" element={<Admin />} />}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </motion.div>
      </Layout>
    </>
  )
}
