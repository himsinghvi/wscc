import { useEffect, useState } from 'react'
import { get, post, put } from '../api/client'

// Create (no `team`) or edit (with `team`) a team. Admin-only — the backend
// re-checks the role, so this modal is only a convenience.
export default function TeamFormModal({ team, onClose, onDone }) {
  const editing = Boolean(team)
  const [f, setF] = useState({
    name: team?.name || '', short_name: team?.short_name || '',
    home_ground_id: team?.home_ground_id || '', color: team?.color || '#4f8cff',
  })
  const [grounds, setGrounds] = useState([])
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const upd = (k, v) => setF((s) => ({ ...s, [k]: v }))

  useEffect(() => { get('/grounds').then((d) => setGrounds(d.grounds)).catch(() => {}) }, [])

  const save = async () => {
    setBusy(true); setErr(null)
    try {
      const payload = { ...f, home_ground_id: f.home_ground_id || null }
      if (editing) await put(`/teams/${team.id}`, payload)
      else await post('/teams', payload)
      onDone()
    } catch (e) { setErr(e.message); setBusy(false) }
  }

  return (
    <div className="modal d-block" style={{ background: 'rgba(0,0,0,.6)' }} onClick={onClose}>
      <div className="modal-dialog modal-dialog-centered" onClick={(e) => e.stopPropagation()}>
        <div className="card wscc w-100"><div className="card-body">
          <div className="d-flex justify-content-between mb-3">
            <h5 className="mb-0">{editing ? 'Edit team' : 'Add team'}</h5>
            <button className="btn-close btn-close-white" onClick={onClose} />
          </div>

          <label className="form-label small text-muted-2">Team name</label>
          <input className="form-control mb-2" value={f.name} onChange={(e) => upd('name', e.target.value)} placeholder="e.g. Harbor Hawks" />

          <div className="row g-2">
            <div className="col-8">
              <label className="form-label small text-muted-2">Short name</label>
              <input className="form-control mb-2" maxLength={4} value={f.short_name}
                onChange={(e) => upd('short_name', e.target.value.toUpperCase())} placeholder="HH" />
            </div>
            <div className="col-4">
              <label className="form-label small text-muted-2">Colour</label>
              <input type="color" className="form-control form-control-color w-100 mb-2" value={f.color}
                onChange={(e) => upd('color', e.target.value)} />
            </div>
          </div>

          <label className="form-label small text-muted-2">Home ground</label>
          <select className="form-select mb-3" value={f.home_ground_id} onChange={(e) => upd('home_ground_id', e.target.value)}>
            <option value="">— none —</option>
            {grounds.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>

          {err && <div className="alert alert-danger small py-2">{err}</div>}
          <button className="btn btn-primary w-100" onClick={save} disabled={busy || !f.name.trim() || !f.short_name.trim()}>
            {busy ? <span className="spinner-border spinner-border-sm" /> : editing ? 'Save changes' : 'Create team'}
          </button>
        </div></div>
      </div>
    </div>
  )
}
