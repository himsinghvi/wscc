import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { get, post } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const dayLabel = (iso) => new Date(iso + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })
let _rid = 1

export default function Scheduler() {
  const { me } = useAuth()
  const [teams, setTeams] = useState([])
  const [grounds, setGrounds] = useState([])
  const [groundRules, setGroundRules] = useState({})
  const [eligible, setEligible] = useState(null)
  const [excluded, setExcluded] = useState(new Set())
  const [rotation, setRotation] = useState('balanced')
  const [date, setDate] = useState('')
  const [fixtures, setFixtures] = useState([])   // {id, home_team_id, away_team_id, ground_id, date}
  const [ai, setAi] = useState(null)
  const [busy, setBusy] = useState(false)
  const [applied, setApplied] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    get('/teams').then((d) => setTeams(d.teams)).catch(() => {})
    get('/grounds').then((d) => setGrounds(d.grounds)).catch(() => {})
    get('/day-rules').then((d) => setGroundRules(d.rules?.ground || {})).catch(() => {})
    get('/scheduler/eligible').then((d) => { setEligible(d); if (d.dates?.length) setDate(d.dates[0]) }).catch(() => {})
  }, [])

  const WD = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
  const weekday = (iso) => iso ? WD[(new Date(iso + 'T00:00').getDay() + 6) % 7] : null
  const groundsForDate = (iso) => {
    const day = weekday(iso)
    return grounds.filter((g) => { const r = groundRules[g.id] || []; return !r.includes('ANY') && !r.includes(day) })
  }

  const tName = (id) => teams.find((t) => t.id === id)?.short_name || teams.find((t) => t.id === id)?.name || '—'
  const dates = eligible?.dates || []
  const respondents = (eligible?.teams || []).map((t) => t.id)
  const included = respondents.filter((id) => !excluded.has(id)).length
  const toggleTeam = (id) => setExcluded((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })

  const generate = async () => {
    setBusy(true); setErr(null); setApplied(null)
    try {
      const r = await post('/scheduler/generate', { exclude_team_ids: [...excluded], ground_rotation: rotation, date })
      setFixtures(r.fixtures.map((f) => ({ id: _rid++, home_team_id: f.home_team_id, away_team_id: f.away_team_id, ground_id: f.ground_id, date: r.date })))
      setAi(r)
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const addRow = () => setFixtures((f) => [...f, {
    id: _rid++, home_team_id: '', away_team_id: '', ground_id: '', date: date || dates[0] || '',
  }])
  const updateRow = (id, k, v) => setFixtures((f) => f.map((x) => x.id === id ? { ...x, [k]: v } : x))
  const removeRow = (id) => setFixtures((f) => f.filter((x) => x.id !== id))

  // conflict detection: a team must not repeat an opponent or a ground this weekend
  const pairCount = {}, teamGround = {}
  for (const f of fixtures) {
    if (f.home_team_id && f.away_team_id) {
      const k = [f.home_team_id, f.away_team_id].sort().join('|'); pairCount[k] = (pairCount[k] || 0) + 1
    }
    for (const t of [f.home_team_id, f.away_team_id]) {
      if (t && f.ground_id) { (teamGround[t] ||= {})[f.ground_id] = (teamGround[t][f.ground_id] || 0) + 1 }
    }
  }
  const rowIssues = (f) => {
    const issues = []
    if (f.home_team_id && f.home_team_id === f.away_team_id) issues.push('same team')
    if (f.home_team_id && f.away_team_id && pairCount[[f.home_team_id, f.away_team_id].sort().join('|')] > 1) issues.push('duplicate fixture')
    for (const t of [f.home_team_id, f.away_team_id]) if (t && f.ground_id && teamGround[t][f.ground_id] > 1) issues.push(`${tName(t)} double-booked ground`)
    return [...new Set(issues)]
  }
  const hasConflicts = fixtures.some((f) => rowIssues(f).length)
  const incomplete = fixtures.some((f) => !f.home_team_id || !f.away_team_id)

  const applySchedule = async () => {
    setBusy(true); setErr(null); setApplied(null)
    try {
      const payload = fixtures.map((f) => ({ home_team_id: f.home_team_id, away_team_id: f.away_team_id, ground_id: f.ground_id || null, date: f.date }))
      const r = await post('/scheduler/apply', { fixtures: payload })
      setApplied(r)
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const TeamOpt = ({ value, onChange }) => (
    <select className="form-select form-select-sm" value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">— team —</option>
      {teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
    </select>
  )

  return (
    <>
      <h3 className="fw-bold mb-1"><i className="bi bi-cpu-fill me-2 text-primary" />Schedule builder</h3>
      <div className="text-muted-2 small mb-4">
        Generate a fair round-robin from poll respondents, then <b>edit it</b> or build one by hand.
        A team never gets the same opponent or ground twice in the weekend.
      </div>

      {/* Generator controls */}
      <div className="card wscc mb-3"><div className="card-body">
        <div className="d-flex justify-content-between flex-wrap gap-2 mb-2">
          <h6 className="mb-0">Auto-generate</h6>
          <div className="d-flex gap-2 flex-wrap">
            <div className="btn-group btn-group-sm">
              {dates.map((d) => <button key={d} className={`btn ${date === d ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setDate(d)}>{dayLabel(d)}</button>)}
            </div>
            <div className="btn-group btn-group-sm">
              <button className={`btn ${rotation === 'balanced' ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setRotation('balanced')}>Rotate grounds</button>
              <button className={`btn ${rotation === 'home' ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setRotation('home')}>Home grounds</button>
            </div>
          </div>
        </div>
        {respondents.length === 0 ? (
          <div className="text-muted-2 small">No teams have responded to the poll yet — you can still build a schedule manually below.</div>
        ) : (
          <>
            <div className="small text-muted-2 mb-1">Responding teams ({included} of {respondents.length} in):</div>
            <div className="d-flex flex-wrap gap-2 mb-3">
              {(eligible?.teams || []).map((t) => {
                const on = !excluded.has(t.id)
                return <button key={t.id} onClick={() => toggleTeam(t.id)} className={`btn btn-sm ${on ? 'btn-primary' : 'btn-outline-light'}`}
                  style={on ? {} : { opacity: 0.5, textDecoration: 'line-through' }}>{t.short}</button>
              })}
            </div>
          </>
        )}
        <div className="d-flex gap-2">
          <motion.button className="btn btn-primary" onClick={generate} disabled={busy || included < 2} whileTap={{ scale: 0.97 }}>
            {busy ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-magic me-1" />Generate</>}
          </motion.button>
          <button className="btn btn-outline-light" onClick={addRow}><i className="bi bi-plus-lg me-1" />Add fixture</button>
          {fixtures.length > 0 && <button className="btn btn-outline-light" onClick={() => { setFixtures([]); setAi(null) }}>Clear</button>}
        </div>
      </div></div>

      {/* Editable fixtures */}
      <div className="row g-4">
        <div className="col-lg-8">
          <div className="card wscc"><div className="card-body">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h6 className="mb-0">Fixtures <span className="text-muted-2 small">({fixtures.length})</span></h6>
              {hasConflicts && <span className="pill pill-closed"><i className="bi bi-exclamation-triangle-fill" /> conflicts</span>}
            </div>

            {fixtures.length === 0 && <div className="text-muted-2 small">No fixtures yet — generate or add one.</div>}

            <AnimatePresence initial={false}>
              {fixtures.map((f) => {
                const issues = rowIssues(f)
                return (
                  <motion.div key={f.id} layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, height: 0 }}
                    className="rounded-3 p-2 mb-2" style={{
                      background: 'rgba(7,12,24,.5)',
                      border: `1px solid ${issues.length ? 'rgba(251,106,106,.5)' : 'var(--border-soft)'}`,
                    }}>
                    <div className="row g-2 align-items-center">
                      <div className="col-12 col-md"><TeamOpt value={f.home_team_id} onChange={(v) => updateRow(f.id, 'home_team_id', v)} /></div>
                      <div className="col-auto text-muted-2 small">vs</div>
                      <div className="col-12 col-md"><TeamOpt value={f.away_team_id} onChange={(v) => updateRow(f.id, 'away_team_id', v)} /></div>
                      <div className="col-6 col-md">
                        {(() => {
                          const avail = groundsForDate(f.date)
                          const cur = grounds.find((g) => g.id === f.ground_id)
                          const curUnavailable = f.ground_id && !avail.some((g) => g.id === f.ground_id)
                          return (
                            <select className="form-select form-select-sm" value={f.ground_id || ''} onChange={(e) => updateRow(f.id, 'ground_id', e.target.value)}>
                              <option value="">— ground —</option>
                              {avail.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                              {curUnavailable && <option value={f.ground_id}>{cur?.name || 'ground'} (unavailable)</option>}
                            </select>
                          )
                        })()}
                      </div>
                      <div className="col-6 col-md-auto">
                        <select className="form-select form-select-sm" value={f.date} onChange={(e) => updateRow(f.id, 'date', e.target.value)}>
                          {(dates.length ? dates : [f.date]).map((d) => <option key={d} value={d}>{dayLabel(d)}</option>)}
                        </select>
                      </div>
                      <div className="col-auto"><button className="btn btn-sm btn-outline-light" onClick={() => removeRow(f.id)}><i className="bi bi-trash" /></button></div>
                    </div>
                    {issues.length > 0 && <div className="small mt-1" style={{ color: 'var(--red)' }}><i className="bi bi-exclamation-circle me-1" />{issues.join(' · ')}</div>}
                  </motion.div>
                )
              })}
            </AnimatePresence>

            {fixtures.length > 0 && (
              <div className="d-flex align-items-center gap-3 mt-3">
                <button className="btn btn-wa" onClick={applySchedule} disabled={busy || hasConflicts || incomplete}>
                  <i className="bi bi-calendar-plus me-1" />Apply schedule
                </button>
                {hasConflicts && <span className="text-danger small">Resolve conflicts first.</span>}
                {incomplete && !hasConflicts && <span className="text-muted-2 small">Fill in every fixture's teams.</span>}
                {applied && <span className="text-success small"><i className="bi bi-check-circle me-1" />Created {applied.created} matches</span>}
              </div>
            )}
            {err && <div className="alert alert-danger mt-3 small mb-0">{err}</div>}
          </div></div>
        </div>

        <div className="col-lg-4">
          <div className="card wscc h-100"><div className="card-body">
            <h6 className="mb-3"><i className="bi bi-robot me-1" />AI explanation
              {ai && <span className="badge text-bg-secondary ms-2">{ai.ai_source}</span>}</h6>
            {!ai ? <div className="text-muted-2 small">Generate a schedule to see the AI's fairness rationale, or build one manually.</div> : (
              <>
                <div className="d-flex gap-2 mb-2 flex-wrap">
                  <span className="pill pill-wait">fairness {ai.fairness_score}</span>
                  {ai.excluded_teams?.length > 0 && <span className="pill pill-closed">{ai.excluded_teams.length} teams disabled</span>}
                </div>
                <pre className="small text-muted-2" style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{ai.ai_explanation}</pre>
              </>
            )}
          </div></div>
        </div>
      </div>
    </>
  )
}
