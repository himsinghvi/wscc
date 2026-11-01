import { useState } from 'react'
import { post, put } from '../api/client'

const PITCHES = ['turf', 'matting', 'astro', 'concrete']

// Create (no `ground`) or edit (with `ground`) a ground. Admin-only.
export default function GroundFormModal({ ground, onClose, onDone }) {
  const editing = Boolean(ground)
  const [f, setF] = useState({
    name: ground?.name || '', city: ground?.city || '',
    pitch_type: ground?.pitch_type || 'turf', address: ground?.address || '',
    notes: ground?.notes || '', lat: ground?.lat ?? '', lng: ground?.lng ?? '',
  })
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const upd = (k, v) => setF((s) => ({ ...s, [k]: v }))

  const save = async () => {
    setBusy(true); setErr(null)
    try {
      const payload = {
        ...f,
        lat: f.lat === '' ? null : Number(f.lat),
        lng: f.lng === '' ? null : Number(f.lng),
      }
      if (editing) await put(`/grounds/${ground.id}`, payload)
      else await post('/grounds', payload)
      onDone()
    } catch (e) { setErr(e.message); setBusy(false) }
  }

  return (
    <div className="modal d-block" style={{ background: 'rgba(0,0,0,.6)' }} onClick={onClose}>
      <div className="modal-dialog modal-dialog-centered" onClick={(e) => e.stopPropagation()}>
        <div className="card wscc w-100"><div className="card-body">
          <div className="d-flex justify-content-between mb-3">
            <h5 className="mb-0">{editing ? 'Edit ground' : 'Add ground'}</h5>
            <button className="btn-close btn-close-white" onClick={onClose} />
          </div>

          <label className="form-label small text-muted-2">Ground name</label>
          <input className="form-control mb-2" value={f.name} onChange={(e) => upd('name', e.target.value)} placeholder="e.g. Lakeside Turf" />

          <div className="row g-2">
            <div className="col-7">
              <label className="form-label small text-muted-2">City</label>
              <input className="form-control mb-2" value={f.city} onChange={(e) => upd('city', e.target.value)} />
            </div>
            <div className="col-5">
              <label className="form-label small text-muted-2">Pitch</label>
              <select className="form-select mb-2 text-capitalize" value={f.pitch_type} onChange={(e) => upd('pitch_type', e.target.value)}>
                {PITCHES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          <label className="form-label small text-muted-2">Address</label>
          <input className="form-control mb-2" value={f.address} onChange={(e) => upd('address', e.target.value)} />

          <div className="row g-2">
            <div className="col"><label className="form-label small text-muted-2">Latitude</label>
              <input className="form-control mb-2" value={f.lat} onChange={(e) => upd('lat', e.target.value)} placeholder="optional" /></div>
            <div className="col"><label className="form-label small text-muted-2">Longitude</label>
              <input className="form-control mb-2" value={f.lng} onChange={(e) => upd('lng', e.target.value)} placeholder="optional" /></div>
          </div>

          <label className="form-label small text-muted-2">Notes</label>
          <textarea className="form-control mb-3" rows="2" value={f.notes} onChange={(e) => upd('notes', e.target.value)} placeholder="Pitch behaviour, boundaries…" />

          {err && <div className="alert alert-danger small py-2">{err}</div>}
          <button className="btn btn-primary w-100" onClick={save} disabled={busy || !f.name.trim()}>
            {busy ? <span className="spinner-border spinner-border-sm" /> : editing ? 'Save changes' : 'Create ground'}
          </button>
        </div></div>
      </div>
    </div>
  )
}
