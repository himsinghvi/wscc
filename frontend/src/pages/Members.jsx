import { useEffect, useState } from 'react'
import { get } from '../api/client'

const BADGE = { admin: 'text-bg-danger', approved: 'text-bg-success', pending: 'text-bg-primary',
  rejected: 'text-bg-secondary', registered: 'text-bg-warning' }

export default function Members() {
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')
  const [err, setErr] = useState(null)

  useEffect(() => { get('/admin/members').then(setData).catch((e) => setErr(e.message)) }, [])
  if (err) return <div className="alert alert-danger">{err}</div>
  if (!data) return <div className="spinner-border text-primary" />

  const fmt = (d) => d ? new Date(d).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—'
  const all = data.members
  const shown = all.filter((m) => !q || [m.email, m.full_name, m.team].some((v) => (v || '').toLowerCase().includes(q.toLowerCase())))
  const counts = all.reduce((a, m) => ({ ...a, [m.status]: (a[m.status] || 0) + 1 }), {})

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-1">
        <h3 className="fw-bold mb-0">Members</h3>
        <span className="text-muted-2 small">{data.count} registered</span>
      </div>
      <div className="text-muted-2 small mb-3">
        Everyone registered on the app. <i className="bi bi-shield-lock me-1" />Passwords are stored one-way hashed and can never be shown.
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3">
        {Object.entries(counts).map(([s, n]) => (
          <span key={s} className={`badge ${BADGE[s] || 'text-bg-secondary'} text-capitalize`}>{s}: {n}</span>
        ))}
      </div>

      <div className="mb-3" style={{ maxWidth: 360 }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-transparent border-secondary"><i className="bi bi-search text-muted-2" /></span>
          <input className="form-control" placeholder="Search name, email or team" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="card wscc"><div className="card-body p-0">
        <div className="table-responsive">
          <table className="table table-sm align-middle mb-0">
            <thead><tr className="text-muted-2 small">
              <th className="ps-3">User</th><th>Team</th><th>Role</th><th>Status</th><th>Last sign-in</th><th>Contact</th>
            </tr></thead>
            <tbody>
                {shown.map((m) => (
                  <tr key={m.email}>
                    <td className="ps-3">
                      <div className="fw-semibold small">{m.full_name || '—'}</div>
                      <div className="text-muted-2" style={{ fontSize: '.72rem' }}>{m.email}</div>
                    </td>
                    <td className="small">{m.team || '—'}</td>
                    <td className="small text-capitalize">{m.role || '—'}</td>
                    <td><span className={`badge ${BADGE[m.status] || 'text-bg-secondary'} text-capitalize`}>{m.status}</span></td>
                    <td className="small mono text-muted-2">{fmt(m.last_sign_in)}</td>
                    <td className="small">
                      {m.phone ? <a href={`tel:${m.phone}`} className="me-2"><i className="bi bi-telephone" /></a> : null}
                      {m.whatsapp ? <a href={`https://wa.me/${(m.whatsapp || '').replace(/\D/g, '')}`} target="_blank" rel="noreferrer" style={{ color: '#25d366' }}><i className="bi bi-whatsapp" /></a> : null}
                      {!m.phone && !m.whatsapp ? <span className="text-muted-2">—</span> : null}
                    </td>
                  </tr>
                ))}
              {shown.length === 0 && <tr><td colSpan={6} className="text-muted-2 small p-3">No members.</td></tr>}
            </tbody>
          </table>
        </div>
      </div></div>
    </>
  )
}
