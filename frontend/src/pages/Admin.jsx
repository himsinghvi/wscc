import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { get, put, post } from '../api/client'
import { useAuth } from '../auth/AuthContext'

// Features 4 & 6: admin-configurable backout day/time and max voting teams.
export default function Admin() {
  const { supabaseEnabled } = useAuth()
  const [cfg, setCfg] = useState(null)
  const [saved, setSaved] = useState(false)
  const [err, setErr] = useState(null)

  useEffect(() => { get('/admin/config').then(setCfg).catch((e) => setErr(e.message)) }, [])

  const update = (k, v) => setCfg((c) => ({ ...c, [k]: v }))

  const save = async () => {
    setErr(null); setSaved(false)
    try {
      await put('/admin/config', {
        max_voting_teams: Number(cfg.max_voting_teams),
        max_sessions_per_team: Number(cfg.max_sessions_per_team),
        vote_open_time: cfg.vote_open_time,
        publish_time: cfg.publish_time,
        backout_weekday: Number(cfg.backout_weekday),
        backout_close_time: cfg.backout_close_time,
        session_policy: cfg.session_policy,
        reject_early_votes: cfg.reject_early_votes,
        timezone: cfg.timezone,
      })
      setSaved(true)
    } catch (e) { setErr(e.message) }
  }

  if (!cfg) return <div className="spinner-border text-primary" />
  const DAYS = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <>
      <h3 className="fw-bold mb-4">Admin settings</h3>
      <div className="card wscc" style={{ maxWidth: 720 }}><div className="card-body">
        <div className="row g-3">
          <Field label="Timezone">
            <input className="form-control" value={cfg.timezone || ''} onChange={(e) => update('timezone', e.target.value)} />
          </Field>
          <Field label="Max voting teams (feature 6)">
            <input type="number" min="1" className="form-control" value={cfg.max_voting_teams}
              onChange={(e) => update('max_voting_teams', e.target.value)} />
          </Field>
          <Field label="Max logins per team (feature 2)">
            <input type="number" min="1" max="10" className="form-control" value={cfg.max_sessions_per_team}
              onChange={(e) => update('max_sessions_per_team', e.target.value)} />
          </Field>
          <Field label="Session policy">
            <select className="form-select" value={cfg.session_policy} onChange={(e) => update('session_policy', e.target.value)}>
              <option value="block_new">Block new login</option>
              <option value="evict_oldest">Evict oldest login</option>
            </select>
          </Field>
          <Field label="Vote opens (Mon)">
            <input type="time" step="1" className="form-control" value={cfg.vote_open_time}
              onChange={(e) => update('vote_open_time', e.target.value)} />
          </Field>
          <Field label="Results publish (Mon)">
            <input type="time" step="1" className="form-control" value={cfg.publish_time}
              onChange={(e) => update('publish_time', e.target.value)} />
          </Field>
          <Field label="Backout day (feature 4)">
            <select className="form-select" value={cfg.backout_weekday} onChange={(e) => update('backout_weekday', e.target.value)}>
              {[1, 2, 3, 4, 5, 6, 7].map((d) => <option key={d} value={d}>{DAYS[d]}</option>)}
            </select>
          </Field>
          <Field label="Backout closes at">
            <input type="time" step="1" className="form-control" value={cfg.backout_close_time}
              onChange={(e) => update('backout_close_time', e.target.value)} />
          </Field>
          <div className="col-12">
            <div className="form-check form-switch">
              <input className="form-check-input" type="checkbox" checked={!!cfg.reject_early_votes}
                onChange={(e) => update('reject_early_votes', e.target.checked)} id="rej" />
              <label className="form-check-label small" htmlFor="rej">
                Hard-reject votes before 11:00 (otherwise flag them red)
              </label>
            </div>
          </div>
        </div>

        <div className="d-flex align-items-center gap-3 mt-4">
          <button className="btn btn-primary" onClick={save}><i className="bi bi-save me-1" />Save</button>
          {saved && <span className="text-success small"><i className="bi bi-check-circle me-1" />Saved</span>}
          {err && <span className="text-danger small">{err}</span>}
        </div>
      </div></div>

      {!supabaseEnabled && <SimulatePanel />}
    </>
  )
}

// Dev-only automation: create a live poll, vote for every test team with random
// dates, and auto-build the schedule.
function SimulatePanel() {
  const [num, setNum] = useState(12)
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)

  const run = async () => {
    setBusy(true); setErr(null); setRes(null)
    try { setRes(await post('/dev/simulate', { num_teams: Number(num), generate_schedule: true })) }
    catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  const reset = async () => { setBusy(true); setErr(null); try { await post('/dev/reset', {}); setRes(null) } finally { setBusy(false) } }

  return (
    <div className="card wscc mt-4" style={{ maxWidth: 720 }}><div className="card-body">
      <h5 className="mb-1"><i className="bi bi-dice-5-fill me-2 text-primary" />Testing automation</h5>
      <div className="text-muted-2 small mb-3">
        Creates a live poll, votes on behalf of N test teams with random dates, then auto-builds the schedule.
        Dev mode only.
      </div>
      <div className="d-flex align-items-end gap-2 flex-wrap">
        <div style={{ width: 130 }}>
          <label className="form-label small text-muted-2">Teams</label>
          <input type="number" min="2" max="34" className="form-control" value={num} onChange={(e) => setNum(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={run} disabled={busy}>
          {busy ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-dice-5 me-1" />Simulate poll & votes</>}
        </button>
        <button className="btn btn-outline-light" onClick={reset} disabled={busy}>Reset</button>
      </div>
      {err && <div className="alert alert-danger mt-3 small mb-0">{err}</div>}
      {res && (
        <div className="mt-3">
          <div className="d-flex gap-2 flex-wrap mb-2">
            <span className="pill pill-open">{res.voted_teams} teams voted</span>
            <span className="pill pill-wait">{res.matches_created} matches scheduled</span>
            {res.poll.dates.map((d) => <span key={d} className="badge text-bg-secondary">{new Date(d + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })}</span>)}
          </div>
          <div className="small text-muted-2">
            See it in <Link to="/rankings">Rankings</Link>, <Link to="/scheduler">Schedule builder</Link> and <Link to="/matches">Schedule &amp; Matches</Link>.
          </div>
        </div>
      )}
    </div></div>
  )
}

function Field({ label, children }) {
  return (
    <div className="col-md-6">
      <label className="form-label small text-muted-2">{label}</label>
      {children}
    </div>
  )
}
