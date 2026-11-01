import { useEffect, useState, useCallback } from 'react'
import { get, post, put } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export default function Matches() {
  const { me } = useAuth()
  const [filter, setFilter] = useState('all')
  const [mine, setMine] = useState(false)
  const [matches, setMatches] = useState([])
  const [teams, setTeams] = useState([])
  const [h2h, setH2h] = useState([])
  const [modal, setModal] = useState(null)   // {type:'result'|'schedule', match?}

  const load = useCallback(() => {
    const params = {}
    if (filter !== 'all') params.status = filter
    if (mine && me?.team_id) params.team_id = me.team_id
    get('/matches', Object.keys(params).length ? params : undefined).then((d) => setMatches(d.matches)).catch(() => {})
    get('/matches/head-to-head').then((d) => setH2h(d.head_to_head)).catch(() => {})
  }, [filter, mine, me])

  useEffect(() => { get('/teams').then((d) => setTeams(d.teams)).catch(() => {}) }, [])
  useEffect(() => { load() }, [load])

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <h3 className="fw-bold mb-0">Schedule & Matches</h3>
        {me?.is_admin && (
          <button className="btn btn-primary btn-sm" onClick={() => setModal({ type: 'schedule' })}>
            <i className="bi bi-plus-lg me-1" /> Schedule match
          </button>
        )}
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3">
        <div className="btn-group">
          {['all', 'scheduled', 'played'].map((f) => (
            <button key={f} className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-outline-light'} text-capitalize`}
              onClick={() => setFilter(f)}>{f === 'all' ? 'All' : f === 'scheduled' ? 'Upcoming' : 'Past'}</button>
          ))}
        </div>
        {me?.team_id && !me?.is_admin && (
          <button className={`btn btn-sm ${mine ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setMine((v) => !v)}>
            <i className="bi bi-star-fill me-1" />My team only
          </button>
        )}
      </div>

      <div className="row g-4">
        <div className="col-lg-7">
          <div className="card wscc"><div className="card-body">
            {matches.length === 0 && <div className="text-muted-2 small">No matches.</div>}
            {matches.map((m) => (
              <div key={m.id} className="d-flex align-items-center justify-content-between py-2 border-bottom border-secondary-subtle">
                <div>
                  <div className="fw-semibold">{m.home_team} <span className="text-muted-2">vs</span> {m.away_team}</div>
                  <div className="text-muted-2 small">
                    {m.ground || 'TBD'}
                    {m.home_score && <span className="mono ms-2">{m.home_score} / {m.away_score}</span>}
                  </div>
                  {m.result && <div className="text-success" style={{ fontSize: '.72rem' }}>{m.result}</div>}
                </div>
                <div className="d-flex align-items-center gap-2">
                  <span className={`badge ${m.status === 'played' ? 'text-bg-success' : 'text-bg-primary'}`}>{m.status}</span>
                  {me?.is_admin && m.status === 'scheduled' && (
                    <button className="btn btn-sm btn-outline-light" onClick={() => setModal({ type: 'result', match: m })}>
                      <i className="bi bi-pencil-square" /> Result
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div></div>
        </div>

        <div className="col-lg-5">
          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">Head-to-head (played)</h6>
            <table className="table table-sm table-borderless mb-0 align-middle">
              <tbody>
                {h2h.map((r, i) => (
                  <tr key={i}>
                    <td className="small">{r.pair_names[0]}</td>
                    <td className="text-muted-2 small">vs</td>
                    <td className="small">{r.pair_names[1]}</td>
                    <td className="text-end"><span className="badge text-bg-secondary">{r.played}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div></div>
        </div>
      </div>

      {modal && <MatchModal modal={modal} teams={teams} onClose={() => setModal(null)} onDone={() => { setModal(null); load() }} />}
    </>
  )
}

function MatchModal({ modal, teams, onClose, onDone }) {
  const isResult = modal.type === 'result'
  const m = modal.match
  const [f, setF] = useState(isResult
    ? { home_score: '', away_score: '', winner_id: m.home_team_id, result: '' }
    : { home_team_id: teams[0]?.id, away_team_id: teams[1]?.id, ground_id: '', scheduled_at: '' })
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const upd = (k, v) => setF((s) => ({ ...s, [k]: v }))

  const save = async () => {
    setBusy(true); setErr(null)
    try {
      if (isResult) await put(`/matches/${m.id}/result`, f)
      else await post('/matches/schedule', f)
      onDone()
    } catch (e) { setErr(e.message); setBusy(false) }
  }

  return (
    <div className="modal d-block" style={{ background: 'rgba(0,0,0,.6)' }} onClick={onClose}>
      <div className="modal-dialog modal-dialog-centered" onClick={(e) => e.stopPropagation()}>
        <div className="card wscc w-100"><div className="card-body">
          <div className="d-flex justify-content-between mb-3">
            <h5 className="mb-0">{isResult ? 'Record result' : 'Schedule match'}</h5>
            <button className="btn-close btn-close-white" onClick={onClose} />
          </div>

          {isResult ? (
            <>
              <div className="text-muted-2 small mb-2">{m.home_team} vs {m.away_team}</div>
              <div className="row g-2 mb-2">
                <div className="col"><input className="form-control" placeholder={`${m.home_team} score`} value={f.home_score} onChange={(e) => upd('home_score', e.target.value)} /></div>
                <div className="col"><input className="form-control" placeholder={`${m.away_team} score`} value={f.away_score} onChange={(e) => upd('away_score', e.target.value)} /></div>
              </div>
              <select className="form-select mb-2" value={f.winner_id} onChange={(e) => upd('winner_id', e.target.value)}>
                <option value={m.home_team_id}>{m.home_team} won</option>
                <option value={m.away_team_id}>{m.away_team} won</option>
              </select>
              <input className="form-control mb-3" placeholder="Result summary (e.g. won by 6 runs)" value={f.result} onChange={(e) => upd('result', e.target.value)} />
            </>
          ) : (
            <>
              <select className="form-select mb-2" value={f.home_team_id} onChange={(e) => upd('home_team_id', e.target.value)}>
                {teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
              <select className="form-select mb-2" value={f.away_team_id} onChange={(e) => upd('away_team_id', e.target.value)}>
                {teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
              <input type="datetime-local" className="form-control mb-3" value={f.scheduled_at}
                onChange={(e) => upd('scheduled_at', e.target.value ? new Date(e.target.value).toISOString() : '')} />
            </>
          )}

          {err && <div className="alert alert-danger small py-2">{err}</div>}
          <button className="btn btn-primary w-100" onClick={save} disabled={busy}>
            {busy ? <span className="spinner-border spinner-border-sm" /> : 'Save'}
          </button>
        </div></div>
      </div>
    </div>
  )
}
