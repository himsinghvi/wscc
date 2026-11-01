import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { get } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import FormBadges from '../components/FormBadges'
import StatCard from '../components/StatCard'
import TeamFormModal from '../components/TeamFormModal'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

const tip = { background: '#121c33', border: '1px solid #26324f', borderRadius: 8, color: '#e8eef9' }

export default function TeamDetail() {
  const { id } = useParams()
  const { me } = useAuth()
  const [d, setD] = useState(null)
  const [err, setErr] = useState(null)
  const [editing, setEditing] = useState(false)

  const load = useCallback(() => {
    get(`/teams/${id}`).then(setD).catch((e) => setErr(e.message))
  }, [id])
  useEffect(() => { setD(null); load() }, [load])

  if (err) return <div className="alert alert-danger">{err}</div>
  if (!d) return <div className="spinner-border text-primary" />
  const t = d.team, rec = d.record

  return (
    <>
      <Link to="/teams" className="small text-decoration-none"><i className="bi bi-chevron-left" /> All teams</Link>
      <div className="d-flex align-items-center gap-3 my-3">
        <div className="rounded-circle d-grid" style={{
          width: 64, height: 64, placeItems: 'center', fontWeight: 700, fontSize: '1.4rem',
          background: (t.color || '#4f8cff') + '33', color: t.color || '#4f8cff',
        }}>{t.short_name}</div>
        <div className="flex-grow-1">
          <h3 className="fw-bold mb-0">{t.name}</h3>
          <div className="text-muted-2 small">
            Home: {d.home_ground?.name || '—'} · <FormBadges form={rec.form} />
          </div>
        </div>
        {me?.is_admin && (
          <button className="btn btn-outline-light btn-sm" onClick={() => setEditing(true)}>
            <i className="bi bi-pencil-square me-1" /> Edit
          </button>
        )}
      </div>

      {editing && <TeamFormModal team={t} onClose={() => setEditing(false)} onDone={() => { setEditing(false); load() }} />}

      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-3"><StatCard icon="controller" label="Played" value={rec.played} /></div>
        <div className="col-6 col-lg-3"><StatCard icon="trophy" label="Won" value={rec.won} /></div>
        <div className="col-6 col-lg-3"><StatCard icon="x-circle" label="Lost" value={rec.lost} /></div>
        <div className="col-6 col-lg-3"><StatCard icon="percent" label="Win rate" value={`${rec.win_pct}%`} /></div>
      </div>

      <div className="row g-4">
        <div className="col-lg-7">
          <div className="card wscc mb-4"><div className="card-body">
            <h6 className="mb-3">Record vs each team</h6>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={d.vs_all}>
                <CartesianGrid strokeDasharray="3 3" stroke="#26324f" />
                <XAxis dataKey="opponent" stroke="#9fb0cd" fontSize={11} />
                <YAxis stroke="#9fb0cd" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={tip} />
                <Bar dataKey="played" fill="#4f8cff" radius={[5, 5, 0, 0]} />
                <Bar dataKey="won" fill="#22c55e" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div></div>

          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">Recent & upcoming matches</h6>
            {d.recent_matches.map((m) => (
              <div key={m.id} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
                <div>
                  <div className="fw-semibold small">{m.home_team} <span className="text-muted-2">vs</span> {m.away_team}</div>
                  <div className="text-muted-2" style={{ fontSize: '.72rem' }}>{m.ground || 'TBD'} · {m.result || 'Scheduled'}</div>
                </div>
                <span className={`badge ${m.status === 'played' ? 'text-bg-success' : 'text-bg-primary'}`}>{m.status}</span>
              </div>
            ))}
          </div></div>
        </div>

        <div className="col-lg-5">
          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">Roster <span className="badge text-bg-secondary">{d.roster.length}</span></h6>
            {d.roster.length === 0 && <div className="text-muted-2 small">No roster data.</div>}
            {d.roster.map((p) => (
              <div key={p.id} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
                <div>
                  <div className="small fw-semibold">
                    {p.full_name} {p.is_rep && <i className="bi bi-person-badge text-primary ms-1" title="Team rep" />}
                  </div>
                  <div className="text-muted-2" style={{ fontSize: '.72rem' }}>
                    {[p.batting, p.bowling].filter(Boolean).join(' · ')}
                  </div>
                </div>
                {p.whatsapp && (
                  <a className="btn btn-sm btn-wa" href={`https://wa.me/${(p.whatsapp || '').replace(/\D/g, '')}`}
                    target="_blank" rel="noreferrer"><i className="bi bi-whatsapp" /></a>
                )}
              </div>
            ))}
          </div></div>
        </div>
      </div>
    </>
  )
}
