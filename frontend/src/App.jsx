import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from './auth/AuthContext'
import Aurora from './components/Aurora'
import { pageVariants } from './components/motion'
import Layout from './components/Layout'
import Login from './pages/Login'
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

  if (!me) return (<><Aurora /><Login /></>)

  return (
    <>
      <Aurora />
      <Layout>
        <AnimatePresence mode="wait">
          <motion.div key={location.pathname} variants={pageVariants} initial="initial" animate="enter" exit="exit">
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
              {me.is_admin && <Route path="/poll-schedule" element={<PollSchedule />} />}
              {me.is_admin && <Route path="/day-rules" element={<DayRules />} />}
              {me.is_admin && <Route path="/admin" element={<Admin />} />}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </Layout>
    </>
  )
}
