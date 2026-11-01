import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { get } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import GroundFormModal from '../components/GroundFormModal'

export default function GroundDetail() {
  const { id } = useParams()
  const { me } = useAuth()
  const [d, setD] = useState(null)
  const [err, setErr] = useState(null)
  const [editing, setEditing] = useState(false)

  const load = useCallback(() => { get(`/grounds/${id}`).then(setD).catch((e) => setErr(e.message)) }, [id])
  useEffect(() => { setD(null); load() }, [load])

  if (err) return <div className="alert alert-danger">{err}</div>
  if (!d) return <div className="spinner-border text-primary" />
  const g = d.ground
  const maps = g.lat && g.lng ? `https://www.google.com/maps/search/?api=1&query=${g.lat},${g.lng}`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(g.name + ' ' + (g.city || ''))}`

  return (
    <>
      <Link to="/grounds" className="small text-decoration-none"><i className="bi bi-chevron-left" /> All grounds</Link>
      <div className="d-flex justify-content-between align-items-start my-3 flex-wrap gap-2">
        <div>
          <h3 className="fw-bold mb-0">{g.name}</h3>
          <div className="text-muted-2 small">{g.address || g.city}</div>
        </div>
        <div className="d-flex gap-2">
          <a className="btn btn-outline-light btn-sm" href={maps} target="_blank" rel="noreferrer">
            <i className="bi bi-map me-1" /> Open in Maps
          </a>
          {me?.is_admin && (
            <button className="btn btn-outline-light btn-sm" onClick={() => setEditing(true)}>
              <i className="bi bi-pencil-square me-1" /> Edit
            </button>
          )}
        </div>
      </div>

      {editing && <GroundFormModal ground={g} onClose={() => setEditing(false)} onDone={() => { setEditing(false); load() }} />}

      <div className="row g-4">
        <div className="col-lg-5">
          <div className="card wscc"><div className="card-body">
            <Row label="City" value={g.city} />
            <Row label="Pitch" value={<span className="text-capitalize">{g.pitch_type}</span>} />
            <Row label="Matches hosted" value={d.match_count} />
            <Row label="Home teams" value={d.home_teams.join(', ') || '—'} />
            {g.notes && <><hr className="border-secondary" /><div className="small text-muted-2">{g.notes}</div></>}
          </div></div>
        </div>
        <div className="col-lg-7">
          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">Matches at this ground</h6>
            {d.matches.length === 0 && <div className="text-muted-2 small">No matches recorded here yet.</div>}
            {d.matches.map((m) => (
              <div key={m.id} className="d-flex justify-content-between align-items-center py-2 border-bottom border-secondary-subtle">
                <div>
                  <div className="fw-semibold small">{m.home_team} <span className="text-muted-2">vs</span> {m.away_team}</div>
                  <div className="text-muted-2" style={{ fontSize: '.72rem' }}>{m.result || 'Scheduled'}</div>
                </div>
                <span className={`badge ${m.status === 'played' ? 'text-bg-success' : 'text-bg-primary'}`}>{m.status}</span>
              </div>
            ))}
          </div></div>
        </div>
      </div>
    </>
  )
}

function Row({ label, value }) {
  return (
    <div className="d-flex justify-content-between py-1">
      <span className="text-muted-2 small">{label}</span><span className="small">{value}</span>
    </div>
  )
}
