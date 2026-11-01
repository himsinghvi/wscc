import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { get, post, put, del } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Stagger, StaggerItem } from '../components/motion'

const STATUS_BADGE = { draft: 'text-bg-secondary', upcoming: 'text-bg-primary', live: 'text-bg-success', done: 'text-bg-dark' }
const TABS = ['Overview', 'Polls', 'Fixtures', 'Availability', 'Admins']

export default function Tournaments() {
  const { me } = useAuth()
  const [list, setList] = useState([])
  const [selId, setSelId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [tab, setTab] = useState('Overview')
  const [creating, setCreating] = useState(false)

  const loadList = useCallback(() => get('/tournaments').then((d) => {
    setList(d.tournaments)
    setSelId((cur) => cur || d.tournaments[0]?.id || null)
  }).catch(() => {}), [])
  const loadDetail = useCallback((id) => id && get(`/tournaments/${id}`).then(setDetail).catch(() => {}), [])

  useEffect(() => { loadList() }, [loadList])
  useEffect(() => { loadDetail(selId) }, [selId, loadDetail])
  const refresh = () => loadDetail(selId)

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <h3 className="fw-bold mb-0">Tournaments</h3>
        {me?.is_admin && (
          <button className="btn btn-primary btn-sm" onClick={() => setCreating(true)}>
            <i className="bi bi-plus-lg me-1" /> New tournament
          </button>
        )}
      </div>

      <div className="row g-4">
        <div className="col-lg-4">
          <Stagger>
            {list.map((t) => (
              <StaggerItem key={t.id}>
                <motion.button whileHover={{ x: 4 }} onClick={() => { setSelId(t.id); setTab('Overview') }}
                  className="card wscc w-100 text-start mb-2 border-0"
                  style={selId === t.id ? { outline: '1px solid var(--primary)', boxShadow: '0 0 0 1px var(--primary)' } : {}}>
                  <div className="card-body py-3">
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="fw-semibold">{t.name}</div>
                      <span className={`badge ${STATUS_BADGE[t.status] || 'text-bg-secondary'} text-capitalize`}>{t.status}</span>
                    </div>
                    <div className="text-muted-2 small mt-1">{t.start_date} → {t.end_date}</div>
                    <div className="d-flex gap-2 mt-2">
                      <span className="badge text-bg-secondary text-capitalize">{t.format}</span>
                      <span className="badge text-bg-primary">{t.team_count} teams</span>
                      {t.is_admin && <span className="badge text-bg-success"><i className="bi bi-star-fill me-1" />admin</span>}
                    </div>
                  </div>
                </motion.button>
              </StaggerItem>
            ))}
          </Stagger>
        </div>

        <div className="col-lg-8">
          {!detail ? <div className="spinner-border text-primary" /> : (
            <div className="card wscc"><div className="card-body">
              <TournamentHeader t={detail.tournament} isAdmin={detail.is_admin} />

              <div className="d-flex gap-1 flex-wrap my-3">
                {TABS.map((x) => (
                  <button key={x} className={`btn btn-sm ${tab === x ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setTab(x)}>
                    {x}{x === 'Polls' && detail.polls.length ? ` (${detail.polls.length})` : ''}
                    {x === 'Fixtures' && detail.fixtures.length ? ` (${detail.fixtures.length})` : ''}
                  </button>
                ))}
              </div>

              <AnimatePresence mode="wait">
                <motion.div key={tab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}>
                  {tab === 'Overview' && <Overview d={detail} />}
                  {tab === 'Polls' && <Polls d={detail} tid={selId} onChange={refresh} />}
                  {tab === 'Fixtures' && <Fixtures d={detail} tid={selId} onChange={refresh} />}
                  {tab === 'Availability' && <Availability d={detail} tid={selId} onChange={refresh} />}
                  {tab === 'Admins' && <Admins d={detail} tid={selId} canManage={me?.is_admin} onChange={refresh} />}
                </motion.div>
              </AnimatePresence>
            </div></div>
          )}
        </div>
      </div>

      {creating && <CreateTournamentModal onClose={() => setCreating(false)} onDone={() => { setCreating(false); loadList() }} />}
    </>
  )
}

function TournamentHeader({ t, isAdmin }) {
  return (
    <div className="d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div>
        <h4 className="fw-bold mb-1">{t.name}</h4>
        <div className="text-muted-2 small">
          <span className="text-capitalize">{t.format}</span> · {t.start_date} → {t.end_date}
          {isAdmin && <span className="badge text-bg-success ms-2"><i className="bi bi-star-fill me-1" />you manage this</span>}
        </div>
      </div>
      <span className={`badge ${STATUS_BADGE[t.status] || 'text-bg-secondary'} text-capitalize`}>{t.status}</span>
    </div>
  )
}

function Overview({ d }) {
  return (
    <>
      <p className="text-muted-2">{d.tournament.description}</p>
      <h6 className="mt-3 mb-2">Participating teams</h6>
      <div className="d-flex flex-wrap gap-2">
        {d.teams.map((t) => (
          <span key={t.id} className="pill pill-wait">{t.short} · {t.name}</span>
        ))}
      </div>
    </>
  )
}

function Polls({ d, tid, onChange }) {
  const { me } = useAuth()
  const [adding, setAdding] = useState(false)
  const vote = async (pollId, idx) => { await post(`/tournaments/${tid}/polls/${pollId}/vote`, { option_idx: idx }); onChange() }

  return (
    <>
      {d.is_admin && (
        <button className="btn btn-sm btn-outline-light mb-3" onClick={() => setAdding(true)}>
          <i className="bi bi-plus-lg me-1" />New poll
        </button>
      )}
      {d.polls.length === 0 && <div className="text-muted-2 small">No polls yet.</div>}
      {d.polls.map((p) => (
        <div key={p.id} className="mb-4">
          <div className="fw-semibold mb-2">{p.question} <span className="text-muted-2 small">· {p.total} votes</span></div>
          {p.options.map((o, i) => {
            const pct = p.total ? Math.round((p.votes[i] / p.total) * 100) : 0
            const mine = p.my_vote === i
            return (
              <motion.button key={i} whileTap={{ scale: 0.99 }} onClick={() => vote(p.id, i)}
                className="w-100 text-start border-0 bg-transparent p-0 mb-2">
                <div className="d-flex justify-content-between small mb-1">
                  <span>{mine && <i className="bi bi-check-circle-fill text-success me-1" />}{o}</span>
                  <span className="text-muted-2">{pct}% · {p.votes[i]}</span>
                </div>
                <div className="progress" style={{ height: 8, background: '#0b1324' }}>
                  <motion.div className="progress-bar" initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6 }} style={{ background: mine ? 'linear-gradient(90deg,#34d399,#22d3ee)' : undefined }} />
                </div>
              </motion.button>
            )
          })}
        </div>
      ))}
      {adding && <CreatePollModal tid={tid} onClose={() => setAdding(false)} onDone={() => { setAdding(false); onChange() }} />}
    </>
  )
}

function Fixtures({ d, tid, onChange }) {
  const [busy, setBusy] = useState(false)
  const [meta, setMeta] = useState(null)
  const gen = async () => { setBusy(true); try { const r = await post(`/tournaments/${tid}/fixtures/generate`, {}); setMeta(r); onChange() } finally { setBusy(false) } }

  return (
    <>
      {d.is_admin && (
        <div className="d-flex align-items-center gap-3 mb-3">
          <button className="btn btn-sm btn-primary" onClick={gen} disabled={busy}>
            {busy ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-magic me-1" />Generate round-robin</>}
          </button>
          {meta && <span className="pill pill-open">fairness {meta.fairness_score}</span>}
        </div>
      )}
      {d.fixtures.length === 0 && <div className="text-muted-2 small">No fixtures generated yet.</div>}
      {d.fixtures.map((f) => (
        <div key={f.id} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
          <div>
            <div className="fw-semibold small">{f.home_team} <span className="text-muted-2">vs</span> {f.away_team}</div>
            <div className="text-muted-2" style={{ fontSize: '.72rem' }}>{f.ground || 'TBD'} · met {f.met_before}× before</div>
          </div>
          <span className="badge text-bg-primary">R{f.round}</span>
        </div>
      ))}
    </>
  )
}

function Availability({ d, tid, onChange }) {
  const set = async (available) => { await post(`/tournaments/${tid}/availability`, { available }); onChange() }
  return (
    <>
      {d.my_team_in && (
        <div className="d-flex align-items-center gap-2 mb-3">
          <span className="small text-muted-2">Your team:</span>
          <button className="btn btn-sm btn-wa" onClick={() => set(true)}><i className="bi bi-check-lg me-1" />Available</button>
          <button className="btn btn-sm btn-outline-light" onClick={() => set(false)}><i className="bi bi-x-lg me-1" />Out</button>
        </div>
      )}
      {d.availability.map((a) => (
        <div key={a.team_id} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
          <span className="small">{a.team}</span>
          {a.available === true ? <span className="pill pill-open">in</span>
            : a.available === false ? <span className="pill pill-closed">out</span>
            : <span className="text-muted-2 small">no response</span>}
        </div>
      ))}
    </>
  )
}

function Admins({ d, tid, canManage, onChange }) {
  const [reps, setReps] = useState([])
  const [pick, setPick] = useState('')
  useEffect(() => { if (canManage) get('/directory', { reps_only: false }).then((x) => setReps(x.directory)).catch(() => {}) }, [canManage])

  const add = async () => { if (!pick) return; await post(`/tournaments/${tid}/admins`, null, { player_id: pick }); setPick(''); onChange() }
  const remove = async (pid) => { await del(`/tournaments/${tid}/admins/${pid}`); onChange() }

  return (
    <>
      <div className="text-muted-2 small mb-2">League admins can appoint players as admins for this tournament only.</div>
      {d.admins.length === 0 && <div className="text-muted-2 small mb-2">No per-tournament admins yet.</div>}
      {d.admins.map((a) => (
        <div key={a.player_id} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
          <span><i className="bi bi-person-badge text-primary me-2" />{a.name}</span>
          {canManage && <button className="btn btn-sm btn-outline-light" onClick={() => remove(a.player_id)}><i className="bi bi-x" /></button>}
        </div>
      ))}
      {canManage && (
        <div className="d-flex gap-2 mt-3">
          <select className="form-select form-select-sm" value={pick} onChange={(e) => setPick(e.target.value)}>
            <option value="">Appoint a player…</option>
            {reps.map((r) => <option key={r.player_id} value={r.player_id}>{r.name} ({r.team})</option>)}
          </select>
          <button className="btn btn-sm btn-primary" onClick={add} disabled={!pick}>Add</button>
        </div>
      )}
    </>
  )
}

/* ---------- modals ---------- */
function Modal({ title, onClose, children }) {
  return (
    <div className="modal d-block" style={{ background: 'rgba(0,0,0,.6)' }} onClick={onClose}>
      <motion.div className="modal-dialog modal-dialog-centered" onClick={(e) => e.stopPropagation()}
        initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
        <div className="card wscc w-100"><div className="card-body">
          <div className="d-flex justify-content-between mb-3"><h5 className="mb-0">{title}</h5>
            <button className="btn-close btn-close-white" onClick={onClose} /></div>
          {children}
        </div></div>
      </motion.div>
    </div>
  )
}

function CreateTournamentModal({ onClose, onDone }) {
  const [f, setF] = useState({ name: '', description: '', format: 'league', start_date: '', end_date: '' })
  const [teams, setTeams] = useState([])
  const [picked, setPicked] = useState([])
  const [err, setErr] = useState(null); const [busy, setBusy] = useState(false)
  useEffect(() => { get('/teams').then((d) => setTeams(d.teams)).catch(() => {}) }, [])
  const toggle = (id) => setPicked((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id])
  const upd = (k, v) => setF((s) => ({ ...s, [k]: v }))
  const save = async () => {
    setBusy(true); setErr(null)
    try { await post('/tournaments', { ...f, team_ids: picked }); onDone() }
    catch (e) { setErr(e.message); setBusy(false) }
  }
  return (
    <Modal title="New tournament" onClose={onClose}>
      <input className="form-control mb-2" placeholder="Name" value={f.name} onChange={(e) => upd('name', e.target.value)} />
      <textarea className="form-control mb-2" rows="2" placeholder="Description" value={f.description} onChange={(e) => upd('description', e.target.value)} />
      <div className="row g-2 mb-2">
        <div className="col"><select className="form-select text-capitalize" value={f.format} onChange={(e) => upd('format', e.target.value)}>
          <option value="league">league</option><option value="knockout">knockout</option><option value="mixed">mixed</option></select></div>
        <div className="col"><input type="date" className="form-control" value={f.start_date} onChange={(e) => upd('start_date', e.target.value)} /></div>
        <div className="col"><input type="date" className="form-control" value={f.end_date} onChange={(e) => upd('end_date', e.target.value)} /></div>
      </div>
      <div className="small text-muted-2 mb-1">Participating teams</div>
      <div className="d-flex flex-wrap gap-2 mb-3">
        {teams.map((t) => (
          <button key={t.id} onClick={() => toggle(t.id)}
            className={`btn btn-sm ${picked.includes(t.id) ? 'btn-primary' : 'btn-outline-light'}`}>{t.short_name}</button>
        ))}
      </div>
      {err && <div className="alert alert-danger small py-2">{err}</div>}
      <button className="btn btn-primary w-100" onClick={save} disabled={busy || !f.name.trim()}>
        {busy ? <span className="spinner-border spinner-border-sm" /> : 'Create tournament'}</button>
    </Modal>
  )
}

function CreatePollModal({ tid, onClose, onDone }) {
  const [q, setQ] = useState(''); const [opts, setOpts] = useState(['', ''])
  const [err, setErr] = useState(null); const [busy, setBusy] = useState(false)
  const setOpt = (i, v) => setOpts((o) => o.map((x, j) => j === i ? v : x))
  const save = async () => {
    setBusy(true); setErr(null)
    try { await post(`/tournaments/${tid}/polls`, { question: q, options: opts.filter((o) => o.trim()) }); onDone() }
    catch (e) { setErr(e.message); setBusy(false) }
  }
  return (
    <Modal title="New poll" onClose={onClose}>
      <input className="form-control mb-2" placeholder="Question" value={q} onChange={(e) => setQ(e.target.value)} />
      {opts.map((o, i) => (
        <input key={i} className="form-control mb-2" placeholder={`Option ${i + 1}`} value={o} onChange={(e) => setOpt(i, e.target.value)} />
      ))}
      <button className="btn btn-sm btn-outline-light mb-3" onClick={() => setOpts((o) => [...o, ''])}><i className="bi bi-plus" /> Add option</button>
      {err && <div className="alert alert-danger small py-2">{err}</div>}
      <button className="btn btn-primary w-100" onClick={save} disabled={busy || !q.trim() || opts.filter((o) => o.trim()).length < 2}>
        {busy ? <span className="spinner-border spinner-border-sm" /> : 'Create poll'}</button>
    </Modal>
  )
}
