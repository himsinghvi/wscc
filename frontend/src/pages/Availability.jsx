import { useEffect, useState } from 'react'
import { get, post } from '../api/client'

const dayLabel = (iso) => new Date(iso + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })

export default function Availability() {
  const [status, setStatus] = useState(null)
  const [note, setNote] = useState('')
  const [sel, setSel] = useState(null)        // Set of selected dates
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [err, setErr] = useState(null)

  const refresh = () => get('/availability/status').then((s) => {
    setStatus(s)
    if (sel === null) setSel(new Set(s.dates || []))  // default: available all polled dates
  }).catch(() => {})
  useEffect(() => { refresh() }, [])

  const dates = status?.dates || []
  const multi = dates.length > 1
  const toggle = (d) => setSel((p) => { const n = new Set(p); n.has(d) ? n.delete(d) : n.add(d); return n })
  const allOn = sel && dates.length > 0 && dates.every((d) => sel.has(d))
  const toggleAll = () => setSel(allOn ? new Set() : new Set(dates))

  const submit = async () => {
    setBusy(true); setErr(null); setResult(null)
    try {
      const r = await post('/availability/submit', { note, available_dates: [...(sel || [])] })
      setResult(r); refresh()
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  if (!status) return <div className="spinner-border text-primary" />

  return (
    <>
      <h3 className="fw-bold mb-1">Match availability</h3>
      <div className="text-muted-2 small mb-4 d-flex align-items-center gap-2 flex-wrap">
        {status.poll_label}
        {status.source === 'scheduled' && <span className="pill pill-wait"><i className="bi bi-calendar-event-fill" /> scheduled poll</span>}
      </div>

      <div className="row g-4">
        <div className="col-lg-7">
          <div className="card wscc"><div className="card-body">
            {status.has_voted ? (
              <div className="text-center py-3">
                <i className="bi bi-check-circle-fill text-success fs-1" />
                <h5 className="mt-2">Your team has submitted</h5>
                <div className="mono text-muted-2">at {new Date(status.my_submission?.submitted_at).toLocaleString()}</div>
                {status.my_available_dates?.length > 0 && (
                  <div className="d-flex justify-content-center flex-wrap gap-2 mt-3">
                    {status.my_available_dates.map((d) => <span key={d} className="pill pill-open">{dayLabel(d)}</span>)}
                  </div>
                )}
                {status.my_submission?.is_early && (
                  <div className="pill pill-closed mt-3 d-inline-block">Submitted before open — will appear in red</div>
                )}
                <div className="text-muted-2 small mt-3">
                  Need to drop a specific slot or day? Use <b>Backout</b> once results are published.
                </div>
              </div>
            ) : status.vote_open ? (
              <>
                <h5 className="mb-3"><i className="bi bi-unlock text-success me-2" />Voting is open</h5>
                <p className="text-muted-2 small mb-3">
                  {multi ? 'Select the days your team can play.' : "Confirm your team's availability."} Your
                  submission is server-stamped to the millisecond; ranking is first-come.
                </p>

                {multi && (
                  <>
                    <div className="d-flex justify-content-between align-items-center mb-1">
                      <label className="form-label small text-muted-2 mb-0">Available on</label>
                      <button className="btn btn-sm btn-outline-light" onClick={toggleAll}>
                        {allOn ? 'Clear all' : 'All days'}
                      </button>
                    </div>
                    <div className="d-flex flex-wrap gap-2 mb-3">
                      {dates.map((d) => {
                        const on = sel?.has(d)
                        return (
                          <button key={d} onClick={() => toggle(d)}
                            className={`btn btn-sm ${on ? 'btn-success' : 'btn-outline-light'}`}>
                            <i className={`bi bi-${on ? 'check2-square' : 'square'} me-1`} />{dayLabel(d)}
                          </button>
                        )
                      })}
                    </div>
                  </>
                )}

                <textarea className="form-control mb-3" rows="2" placeholder="Optional note (e.g. 10 confirmed players)"
                  value={note} onChange={(e) => setNote(e.target.value)} />
                <button className="btn btn-success btn-lg w-100" onClick={submit} disabled={busy || (multi && !(sel && sel.size))}>
                  {busy ? <span className="spinner-border spinner-border-sm" /> :
                    <><i className="bi bi-hand-thumbs-up me-1" /> {multi ? `We're available (${sel?.size || 0} day${sel?.size === 1 ? '' : 's'})` : "We're available"}</>}
                </button>
              </>
            ) : (
              <div className="text-center py-3">
                <i className="bi bi-lock-fill fs-1" style={{ color: 'var(--amber)' }} />
                <h5 className="mt-2">Voting not open yet</h5>
                <div className="text-muted-2">Opens {new Date(status.vote_open_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</div>
              </div>
            )}
            {result && <div className="alert alert-success mt-3 small mb-0">{result.message}</div>}
            {err && <div className="alert alert-danger mt-3 small mb-0">{err}</div>}
          </div></div>
        </div>

        <div className="col-lg-5">
          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">Poll window</h6>
            <Row label="Teams voted" value={`${status.teams_voted} / ${status.max_voting_teams}`} />
            <Row label="Dates" value={dates.map(dayLabel).join(', ')} />
            <Row label="Slots / day" value={(status.slots || []).join(', ')} />
            <Row label="Voting opens" value={new Date(status.vote_open_at).toLocaleString()} />
            <Row label="Publishes" value={new Date(status.publish_at).toLocaleString()} />
            <Row label="Backout open till" value={new Date(status.backout_close_at).toLocaleString()} />
            <hr className="border-secondary" />
            <div className="small text-muted-2"><i className="bi bi-shield-check me-1" />All timing is validated on the server.</div>
          </div></div>
        </div>
      </div>
    </>
  )
}

function Row({ label, value }) {
  return (
    <div className="d-flex justify-content-between py-1 gap-3">
      <span className="text-muted-2 small flex-shrink-0">{label}</span>
      <span className="small mono text-end">{value}</span>
    </div>
  )
}
