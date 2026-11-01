import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { get } from '../api/client'
import { Stagger, StaggerItem } from '../components/motion'

// Feature 3b: published ordered list. Votes before 11:00 show RED (excluded
// from the valid rank); valid first-come votes show GREEN. Times shown to ms.
export default function Rankings() {
  const [data, setData] = useState(null)

  useEffect(() => { get('/availability/rankings').then(setData).catch(() => {}) }, [])
  if (!data) return <div className="spinner-border text-primary" />

  const dayLabel = (iso) => new Date(iso + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
  // "Sat 7 Nov: 1st, 2nd" per date, from available_slots (falls back to dates)
  const slotBadges = (r) => {
    if (r.available_slots?.length) {
      const g = {}
      for (const t of r.available_slots) { const [d, s] = t.split('#'); (g[d] ||= []).push(s) }
      return Object.entries(g).map(([d, ss]) => `${dayLabel(d)}: ${ss.join(', ')}`)
    }
    return (r.available_dates || []).map(dayLabel)
  }
  const fmt = (iso, ms) => {
    const d = new Date(iso)
    const millis = String(ms % 1000).padStart(3, '0')
    return d.toLocaleTimeString([], { hour12: false }) + '.' + millis
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-1">
        <h3 className="fw-bold mb-0">Availability rankings</h3>
        <div className="d-flex gap-2">
          <span className="pill pill-open"><span className="mono">●</span> on-time</span>
          <span className="pill pill-closed"><span className="mono">●</span> early</span>
        </div>
      </div>
      <div className="text-muted-2 small mb-4">Weekend of {data.weekend_date} · ordered by server submit time</div>

      {!data.published ? (
        <div className="card wscc"><div className="card-body text-center py-5">
          <i className="bi bi-hourglass-split fs-1 text-primary" />
          <h5 className="mt-3">Results publish at {new Date(data.publish_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</h5>
        </div></div>
      ) : data.rows.length === 0 ? (
        <div className="card wscc"><div className="card-body text-center py-5 text-muted-2">
          No submissions recorded for this weekend.
        </div></div>
      ) : (
        <Stagger>
          {data.rows.map((r) => (
            <StaggerItem key={r.team_id} className={`rank-row ${r.color}`}>
              <motion.div className="rank-badge" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 300, damping: 18 }}>
                {r.rank ?? <i className="bi bi-exclamation" />}
              </motion.div>
              <div className="flex-grow-1">
                <div className="fw-semibold">
                  {r.team_name}
                  {r.status === 'backed_out' && <span className="badge text-bg-secondary ms-2">backed out</span>}
                  {r.is_early && <span className="badge text-bg-danger ms-2">early</span>}
                </div>
                {(r.available_slots?.length > 0 || r.available_dates?.length > 0) && (
                  <div className="d-flex flex-wrap gap-1 mt-1">
                    {slotBadges(r).map((b) => (
                      <span key={b} className="badge text-bg-secondary" style={{ fontWeight: 500 }}>{b}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="mono text-muted-2 small text-end flex-shrink-0">{fmt(r.submitted_at, r.submitted_at_ms)}</div>
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </>
  )
}
