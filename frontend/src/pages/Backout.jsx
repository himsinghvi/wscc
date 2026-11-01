import { useEffect, useState } from 'react'
import { get, post } from '../api/client'
import SlotGrid from '../components/SlotGrid'

const dayLabel = (iso) => new Date(iso + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })

// Feature 4: back out of ALL, a whole day, or specific date+slot combos
// (a team may drop only the 2nd slot on one day). Enforced on the server.
export default function Backout() {
  const [status, setStatus] = useState(null)
  const [reason, setReason] = useState('')
  const [sel, setSel] = useState(new Set())   // tokens the team wants to back out of
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)

  const refresh = () => get('/availability/status').then((s) => { setStatus(s); setSel(new Set()) }).catch(() => {})
  useEffect(() => { refresh() }, [])

  const doBackout = async (slots) => {
    if (!slots.length) return
    setBusy(true); setErr(null); setMsg(null)
    try {
      const r = await post('/availability/backout', { reason, slots })
      setMsg(r.status === 'backed_out' ? 'Your team has fully backed out.'
        : `Backed out of ${slots.length} slot${slots.length === 1 ? '' : 's'}.`)
      refresh()
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  if (!status) return <div className="spinner-border text-primary" />
  const opted = status.my_available_slots || []
  const already = status.my_backed_out_slots || []
  const fullyOut = status.my_submission?.status === 'backed_out'
  const toggle = (tok) => setSel((p) => { const n = new Set(p); n.has(tok) ? n.delete(tok) : n.add(tok); return n })
  const groupBadges = (tokens) => {
    const g = {}; for (const t of tokens) { const [d, s] = t.split('#'); (g[d] ||= []).push(s) }
    return Object.entries(g)
  }

  return (
    <>
      <h3 className="fw-bold mb-1">Back out</h3>
      <div className="text-muted-2 small mb-4">{status.poll_label}</div>

      <div className="card wscc" style={{ maxWidth: 640 }}>
        <div className="card-body">
          {already.length > 0 && (
            <div className="mb-3">
              <div className="small text-muted-2 mb-1">Already backed out of:</div>
              <div className="d-flex flex-column gap-1">
                {groupBadges(already).map(([d, ss]) => (
                  <div key={d} className="d-flex justify-content-between"><span className="small">{dayLabel(d)}</span>
                    <span className="d-flex gap-1">{ss.map((s) => <span key={s} className="pill pill-closed">{s}</span>)}</span></div>
                ))}
              </div>
            </div>
          )}

          {!status.has_voted ? (
            <div className="text-muted-2">Your team hasn't submitted availability, so there's nothing to back out of.</div>
          ) : fullyOut ? (
            <div className="text-center py-3"><i className="bi bi-check-circle text-secondary fs-1" /><h5 className="mt-2">Fully backed out</h5></div>
          ) : status.backout_open ? (
            <>
              <div className="rounded-3 p-3 mb-3 d-flex align-items-start gap-2" style={{
                background: 'rgba(251,191,36,.12)', border: '1px solid rgba(251,191,36,.4)', color: '#ffe08a',
              }}>
                <i className="bi bi-exclamation-triangle-fill mt-1" />
                <div className="small">Backout closes <strong>{new Date(status.backout_close_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</strong>. After that it's locked by the server.</div>
              </div>

              <div className="small text-muted-2 mb-2">Tap the slots your team can <b>no longer</b> play:</div>
              <SlotGrid dates={status.dates} slots={status.slots} value={sel} onToggle={toggle}
                allowed={new Set(opted)} tone="backout" />

              <textarea className="form-control my-3" rows="2" placeholder="Reason (optional)"
                value={reason} onChange={(e) => setReason(e.target.value)} />
              <div className="d-flex gap-2">
                <button className="btn btn-danger flex-grow-1" onClick={() => doBackout([...sel])} disabled={busy || sel.size === 0}>
                  {busy ? <span className="spinner-border spinner-border-sm" /> :
                    <><i className="bi bi-box-arrow-left me-1" />Back out of {sel.size || ''} selected</>}
                </button>
                <button className="btn btn-outline-light" onClick={() => doBackout(opted)} disabled={busy}>Back out of all</button>
              </div>
            </>
          ) : (
            <div className="text-center py-3">
              <i className="bi bi-lock-fill fs-1" style={{ color: 'var(--amber)' }} />
              <h5 className="mt-2">Backout window is closed</h5>
              <div className="text-muted-2 small">Closed {new Date(status.backout_close_at).toLocaleString()}</div>
            </div>
          )}
          {msg && <div className="alert alert-success mt-3 small mb-0">{msg}</div>}
          {err && <div className="alert alert-danger mt-3 small mb-0">{err}</div>}
        </div>
      </div>
    </>
  )
}
