import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { get } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import StatCard from '../components/StatCard'
import Countdown from '../components/Countdown'
import { Stagger, StaggerItem, Reveal } from '../components/motion'

const whenLabel = (iso) => iso
  ? new Date(iso).toLocaleString([], { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
  : '—'

const PHASE_UI = {
  before_open: { pill: 'pill-wait', text: 'Voting opens soon', icon: 'hourglass-split' },
  voting_open: { pill: 'pill-open', text: 'Voting is OPEN', icon: 'unlock-fill' },
  backout_open: { pill: 'pill-wait', text: 'Backout window open', icon: 'box-arrow-left' },
  closed: { pill: 'pill-closed', text: 'Voting closed', icon: 'lock-fill' },
}

const QUICK = [
  { to: '/availability', icon: 'calendar-check-fill', title: 'Submit availability', sub: 'Vote for this weekend. First-come ranking in ms.', cap: 'availability.submit' },
  { to: '/rankings', icon: 'bar-chart-steps', title: 'View rankings', sub: 'Published order with exact submit times.' },
  { to: '/scheduler', icon: 'cpu-fill', title: 'AI scheduler', sub: 'Fair round-robin fixtures from availability.', cap: 'schedule.manage' },
]

export default function Dashboard() {
  const { me } = useAuth()
  const [time, setTime] = useState(null)
  const [stats, setStats] = useState(null)
  const [avail, setAvail] = useState(null)

  useEffect(() => {
    get('/meta/time').then(setTime).catch(() => {})
    get('/stats/overview').then(setStats).catch(() => {})
    get('/availability/status').then(setAvail).catch(() => {})
  }, [])

  const caps = new Set(me?.capabilities || [])
  const quick = QUICK.filter((q) => !q.cap || caps.has(q.cap))
  const phase = time && PHASE_UI[time.phase]

  return (
    <>
      {/* Hero */}
      <Reveal className="card wscc mb-4" style={{ background: 'linear-gradient(130deg, rgba(91,140,255,.16), rgba(139,92,246,.10) 55%, rgba(13,20,38,.6))' }}>
        <div className="card-body p-4 position-relative">
          <div className="d-flex justify-content-between align-items-start flex-wrap gap-3">
            <div>
              <div className="text-muted-2 small mb-1"><i className="bi bi-calendar-event me-1" />Weekend of {time?.weekend_date || '—'}</div>
              <h2 className="fw-bold mb-2"><span className="gradient-text">Match weekend</span> at a glance</h2>
              <div className="d-flex gap-2 flex-wrap align-items-center">
                {phase && (
                  <motion.span className={`pill ${phase.pill}`} initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.2 }}>
                    <i className={`bi bi-${phase.icon}`} /> {phase.text}
                  </motion.span>
                )}
                {time?.source === 'scheduled' && (
                  <span className="pill pill-wait"><i className="bi bi-calendar-event-fill" /> {time.poll_label}</span>
                )}
              </div>
            </div>
            <motion.i className="bi bi-trophy-fill d-none d-md-block"
              style={{ fontSize: '3.4rem', color: 'rgba(122,162,255,.35)' }}
              animate={{ y: [0, -8, 0], rotate: [0, -5, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }} />
          </div>

          <div className="row g-3 mt-2">
            <TimeTile icon="unlock" title="Voting opens" when={whenLabel(time?.vote_open_at)}
              body={time && (time.phase === 'before_open'
                ? <Countdown to={time.vote_open_at} label="in" /> : <span className="text-success">Opened</span>)} />
            <TimeTile icon="megaphone" title="Results publish" when={whenLabel(time?.publish_at)}
              body={time && (!time.published
                ? <Countdown to={time.publish_at} label="in" /> : <Link to="/rankings" className="text-success">Published →</Link>)} />
            <TimeTile icon="box-arrow-left" title="Backout open until" when={whenLabel(time?.backout_close_at)}
              body={time && <Countdown to={time.backout_close_at} label="in" />} />
          </div>
        </div>
      </Reveal>

      {/* KPI row */}
      <Stagger className="row g-3 mb-4">
        <StaggerItem className="col-6 col-lg-3"><StatCard icon="people-fill" label="Teams" value={stats?.totals.teams ?? 0} accent="primary" /></StaggerItem>
        <StaggerItem className="col-6 col-lg-3"><StatCard icon="geo-alt-fill" label="Grounds" value={stats?.totals.grounds ?? 0} accent="cyan" /></StaggerItem>
        <StaggerItem className="col-6 col-lg-3"><StatCard icon="trophy-fill" label="Matches played" value={stats?.totals.matches_played ?? 0} accent="green" /></StaggerItem>
        <StaggerItem className="col-6 col-lg-3"><StatCard icon="calendar-check-fill" label="Teams voted"
          value={avail ? `${avail.teams_voted}/${avail.max_voting_teams}` : '—'} accent="amber" sub="this weekend" /></StaggerItem>
      </Stagger>

      {/* Quick actions */}
      <Stagger className="row g-3">
        {quick.map((q) => (
          <StaggerItem className="col-md-6 col-lg-4" key={q.to}>
            <Link to={q.to} className="text-decoration-none">
              <motion.div className="card wscc h-100" whileHover={{ y: -5 }}>
                <div className="card-body">
                  <div className="rounded-3 d-grid mb-3" style={{ width: 44, height: 44, placeItems: 'center', background: 'rgba(91,140,255,.15)', color: 'var(--primary-2)', fontSize: '1.2rem' }}>
                    <i className={`bi bi-${q.icon}`} />
                  </div>
                  <h6 className="mb-1">{q.title}</h6>
                  <div className="text-muted-2 small">{q.sub}</div>
                  <div className="text-primary small mt-2">Open <i className="bi bi-arrow-right" /></div>
                </div>
              </motion.div>
            </Link>
          </StaggerItem>
        ))}
      </Stagger>
    </>
  )
}

function TimeTile({ icon, title, when, body }) {
  return (
    <div className="col-md-4">
      <div className="rounded-3 p-3 h-100" style={{ background: 'rgba(7,12,24,.5)', border: '1px solid var(--border-soft)' }}>
        <div className="text-muted-2 small"><i className={`bi bi-${icon} me-1`} />{title}</div>
        <div className="text-muted-2 mb-1" style={{ fontSize: '.72rem' }}>{when}</div>
        <div className="fs-5 fw-semibold mono">{body}</div>
      </div>
    </div>
  )
}
