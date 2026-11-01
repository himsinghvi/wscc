import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { get, post } from '../api/client'
import { Stagger, StaggerItem } from '../components/motion'

const BADGE = { pending: 'text-bg-primary', approved: 'text-bg-success', rejected: 'text-bg-secondary' }

export default function Approvals() {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(null)
  const [err, setErr] = useState(null)

  const load = useCallback(() => get('/signup/requests').then(setData).catch((e) => setErr(e.message)), [])
  useEffect(() => { load() }, [load])

  const act = async (email, action) => {
    setBusy(email + action); setErr(null)
    try { await post(`/signup/requests/${encodeURIComponent(email)}/${action}`, {}); await load() }
    catch (e) { setErr(e.message) } finally { setBusy(null) }
  }

  if (!data) return <div className="spinner-border text-primary" />
  const reqs = data.requests || []
  const pending = reqs.filter((r) => r.status === 'pending')
  const decided = reqs.filter((r) => r.status !== 'pending')

  return (
    <>
      <h3 className="fw-bold mb-1">Signup approvals</h3>
      <div className="text-muted-2 small mb-4">
        Approve or decline join requests. Max {data.max_per_team} members per team.
      </div>
      {err && <div className="alert alert-danger small">{err}</div>}

      <h6 className="mb-2">Pending <span className="badge text-bg-primary">{pending.length}</span></h6>
      {pending.length === 0 && <div className="text-muted-2 small mb-4">No pending requests.</div>}
      <Stagger className="d-flex flex-column gap-2 mb-4">
        <AnimatePresence>
          {pending.map((r) => (
            <StaggerItem key={r.email}>
              <motion.div layout className="card wscc"><div className="card-body py-2 d-flex align-items-center justify-content-between flex-wrap gap-2">
                <div>
                  <div className="fw-semibold">{r.full_name || r.email}</div>
                  <div className="text-muted-2 small">{r.email} · wants to join <b>{r.team || '—'}</b>
                    {' '}<span className="text-muted-2">({r.team_members}/{data.max_per_team} members)</span></div>
                </div>
                <div className="d-flex gap-2">
                  <button className="btn btn-sm btn-wa" disabled={busy || r.team_full} onClick={() => act(r.email, 'approve')}
                    title={r.team_full ? 'Team already full' : ''}>
                    <i className="bi bi-check-lg me-1" />{r.team_full ? 'Team full' : 'Approve'}
                  </button>
                  <button className="btn btn-sm btn-outline-light" disabled={busy} onClick={() => act(r.email, 'reject')}>
                    <i className="bi bi-x-lg me-1" />Decline
                  </button>
                </div>
              </div></motion.div>
            </StaggerItem>
          ))}
        </AnimatePresence>
      </Stagger>

      {decided.length > 0 && (
        <>
          <h6 className="mb-2 text-muted-2">History</h6>
          {decided.map((r) => (
            <div key={r.email} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
              <span className="small">{r.full_name || r.email} <span className="text-muted-2">· {r.team}</span></span>
              <span className={`badge ${BADGE[r.status]} text-capitalize`}>{r.status}</span>
            </div>
          ))}
        </>
      )}
    </>
  )
}
