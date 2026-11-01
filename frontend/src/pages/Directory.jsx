import { useEffect, useState } from 'react'
import { get } from '../api/client'
import { Stagger, StaggerItem } from '../components/motion'

// Feature 9: 1-click phone / WhatsApp. Search + reps/all toggle.
export default function Directory() {
  const [people, setPeople] = useState([])
  const [repsOnly, setRepsOnly] = useState(true)
  const [q, setQ] = useState('')

  useEffect(() => {
    get('/directory', { reps_only: repsOnly }).then((d) => setPeople(d.directory)).catch(() => {})
  }, [repsOnly])

  const shown = people.filter((p) =>
    !q || [p.name, p.team].some((v) => (v || '').toLowerCase().includes(q.toLowerCase())))

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-1">
        <h3 className="fw-bold mb-0">Team directory</h3>
        <div className="btn-group btn-group-sm">
          <button className={`btn ${repsOnly ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setRepsOnly(true)}>Reps</button>
          <button className={`btn ${!repsOnly ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setRepsOnly(false)}>Everyone</button>
        </div>
      </div>
      <div className="text-muted-2 small mb-3">Reach any team rep in one tap.</div>

      <div className="mb-3" style={{ maxWidth: 360 }}>
        <div className="input-group">
          <span className="input-group-text bg-transparent border-secondary"><i className="bi bi-search text-muted-2" /></span>
          <input className="form-control" placeholder="Search name or team" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <Stagger className="row g-3">
        {shown.map((p, i) => (
          <StaggerItem className="col-md-6 col-lg-4" key={i}>
            <div className="card wscc h-100"><div className="card-body">
              <div className="d-flex justify-content-between align-items-start">
                <div>
                  <div className="fw-semibold">{p.name}
                    {p.is_rep && <i className="bi bi-person-badge text-primary ms-1" title="Team rep" />}
                  </div>
                  <div className="text-muted-2 small">{p.team}</div>
                </div>
                <span className="badge text-bg-secondary">{p.role}</span>
              </div>
              <div className="d-flex gap-2 mt-3">
                {p.call_link && (
                  <a className="btn btn-sm btn-outline-light flex-grow-1" href={p.call_link}>
                    <i className="bi bi-telephone-fill me-1" /> Call
                  </a>
                )}
                {p.whatsapp_link && (
                  <a className="btn btn-sm btn-wa flex-grow-1" href={p.whatsapp_link} target="_blank" rel="noreferrer">
                    <i className="bi bi-whatsapp me-1" /> WhatsApp
                  </a>
                )}
              </div>
            </div></div>
          </StaggerItem>
        ))}
        {shown.length === 0 && <div className="text-muted-2 small">No matches.</div>}
      </Stagger>
    </>
  )
}
