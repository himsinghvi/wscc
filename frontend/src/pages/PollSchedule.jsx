import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { get, post, put, del } from '../api/client'
import { Stagger, StaggerItem } from '../components/motion'
import MultiDateCalendar from '../components/MultiDateCalendar'

const STATE_BADGE = { live: 'text-bg-success', upcoming: 'text-bg-primary', past: 'text-bg-secondary' }
const EMPTY = { label: '', vote_open_at: '', publish_at: '', backout_close_at: '', weekend_date: '', dates: [], slots: [] }
const dayLabel = (iso) => new Date(iso + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })

export default function PollSchedule() {
  const [data, setData] = useState(null)
  const [f, setF] = useState(EMPTY)
  const [editingId, setEditingId] = useState(null)
  const [newSlot, setNewSlot] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => get('/poll-schedule').then(setData).catch(() => {}), [])
  useEffect(() => { load() }, [load])
  const upd = (k, v) => setF((s) => ({ ...s, [k]: v }))

  const removeDate = (d) => upd('dates', f.dates.filter((x) => x !== d))
  const addSlot = () => { const s = newSlot.trim(); if (s && !f.slots.includes(s)) upd('slots', [...f.slots, s]); setNewSlot('') }
  const removeSlot = (s) => upd('slots', f.slots.filter((x) => x !== s))

  const resetForm = () => { setF(EMPTY); setEditingId(null); setErr(null) }

  const startEdit = (p) => {
    setEditingId(p.id)
    setErr(null)
    setF({
      label: p.label || '',
      vote_open_at: (p.vote_open_at || '').slice(0, 16),
      publish_at: (p.publish_at || '').slice(0, 16),
      backout_close_at: (p.backout_close_at || '').slice(0, 16),
      weekend_date: p.weekend_date || '',
      dates: p.dates || [],
      slots: p.slots || [],
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const save = async () => {
    setBusy(true); setErr(null)
    const payload = {
      label: f.label || null,
      vote_open_at: f.vote_open_at,
      publish_at: f.publish_at || null,
      backout_close_at: f.backout_close_at || null,
      weekend_date: f.weekend_date || null,
      dates: f.dates.length ? f.dates : null,
      slots: f.slots.length ? f.slots : null,
    }
    try {
      if (editingId) await put(`/poll-schedule/${editingId}`, payload)
      else await post('/poll-schedule', payload)
      resetForm(); load()
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const remove = async (id) => { await del(`/poll-schedule/${id}`); if (editingId === id) resetForm(); load() }
  const fmt = (iso) => new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })

  return (
    <>
      <h3 className="fw-bold mb-1">Poll schedule</h3>
      <div className="text-muted-2 small mb-4">
        Schedule an availability poll at an exact date & time and choose which <b>match dates</b> you're
        collecting availability for. Teams then pick which of those dates they can play. A live/upcoming
        scheduled round <b>overrides</b> the weekly default.{data && <> Times are in <b>{data.timezone}</b>.</>}
      </div>

      <div className="row g-4">
        <div className="col-lg-5">
          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">
              <i className={`bi bi-${editingId ? 'pencil-square' : 'calendar-plus'} me-2 text-primary`} />
              {editingId ? 'Edit scheduled poll' : 'New scheduled poll'}
            </h6>

            <label className="form-label small text-muted-2">Label</label>
            <input className="form-control mb-2" placeholder="e.g. Diwali special weekend" value={f.label} onChange={(e) => upd('label', e.target.value)} />

            <label className="form-label small text-muted-2">Voting opens *</label>
            <input type="datetime-local" className="form-control mb-2" value={f.vote_open_at} onChange={(e) => upd('vote_open_at', e.target.value)} />

            <div className="row g-2">
              <div className="col">
                <label className="form-label small text-muted-2">Results publish</label>
                <input type="datetime-local" className="form-control mb-1" value={f.publish_at} onChange={(e) => upd('publish_at', e.target.value)} />
              </div>
              <div className="col">
                <label className="form-label small text-muted-2">Backout open until</label>
                <input type="datetime-local" className="form-control mb-1" value={f.backout_close_at} onChange={(e) => upd('backout_close_at', e.target.value)} />
              </div>
            </div>
            <div className="text-muted-2 mb-2" style={{ fontSize: '.72rem' }}>
              <i className="bi bi-info-circle me-1" />Backout opens when results publish and stays open until this
              exact date & time. Leave it blank to default to the end of the last match date.
            </div>

            <label className="form-label small text-muted-2 d-flex justify-content-between">
              <span>Dates asking availability for</span>
              {f.dates.length > 0 && <span className="text-primary">{f.dates.length} selected</span>}
            </label>
            <MultiDateCalendar value={f.dates} onChange={(d) => upd('dates', d)} />
            {f.dates.length > 0 && (
              <div className="d-flex flex-wrap gap-2 mt-2">
                {f.dates.map((d) => (
                  <span key={d} className="pill pill-wait">{dayLabel(d)}
                    <i className="bi bi-x-lg ms-1" role="button" onClick={() => removeDate(d)} /></span>
                ))}
                <button type="button" className="btn btn-sm btn-outline-light" onClick={() => upd('dates', [])}>Clear</button>
              </div>
            )}
            <div className="text-muted-2 mb-3 mt-2" style={{ fontSize: '.72rem' }}>
              <i className="bi bi-info-circle me-1" />Click days in the calendar to select multiple match dates.
              Leave empty to poll a single weekend (next Saturday). Publish/backout default to open +6h / +3 days.
            </div>

            <label className="form-label small text-muted-2">Slots per day</label>
            <div className="d-flex gap-2 mb-2">
              <input className="form-control" placeholder="e.g. 1st" value={newSlot}
                onChange={(e) => setNewSlot(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSlot() } }} />
              <button type="button" className="btn btn-outline-light" onClick={addSlot} disabled={!newSlot.trim()}><i className="bi bi-plus-lg" /></button>
            </div>
            <div className="d-flex flex-wrap gap-2 mb-1">
              {(f.slots.length ? f.slots : ['1st', '2nd']).map((s) => (
                <span key={s} className={`pill ${f.slots.length ? 'pill-wait' : 'pill-open'}`}>{s}
                  {f.slots.length > 0 && <i className="bi bi-x-lg ms-1" role="button" onClick={() => removeSlot(s)} />}</span>
              ))}
            </div>
            <div className="text-muted-2 mb-3" style={{ fontSize: '.72rem' }}>
              <i className="bi bi-info-circle me-1" />Teams respond per date <b>and</b> slot. Default is 1st / 2nd if left empty.
            </div>

            {err && <div className="alert alert-danger small py-2">{err}</div>}
            <div className="d-flex gap-2">
              <button className="btn btn-primary flex-grow-1" onClick={save} disabled={busy || !f.vote_open_at}>
                {busy ? <span className="spinner-border spinner-border-sm" /> : editingId ? 'Save changes' : 'Schedule poll'}
              </button>
              {editingId && <button className="btn btn-outline-light" onClick={resetForm}>Cancel</button>}
            </div>
          </div></div>
        </div>

        <div className="col-lg-7">
          <div className="card wscc"><div className="card-body">
            <h6 className="mb-3">Scheduled rounds</h6>
            {!data ? <div className="spinner-border text-primary" /> :
              data.polls.length === 0 ? <div className="text-muted-2 small">None scheduled — the weekly default is in effect.</div> : (
              <AnimatePresence>
                <Stagger className="d-flex flex-column gap-2">
                  {data.polls.map((p) => (
                    <StaggerItem key={p.id}>
                      <motion.div layout className="rounded-3 p-3" style={{
                        background: 'rgba(7,12,24,.5)', border: '1px solid var(--border-soft)',
                        borderLeft: p.is_current ? '3px solid var(--primary)' : '1px solid var(--border-soft)',
                      }}>
                        <div className="d-flex justify-content-between align-items-start flex-wrap gap-2">
                          <div>
                            <div className="fw-semibold">
                              {p.label}
                              {p.is_current && <span className="badge text-bg-primary ms-2"><i className="bi bi-star-fill me-1" />current</span>}
                              <span className={`badge ${STATE_BADGE[p.state]} ms-2 text-capitalize`}>{p.state}</span>
                            </div>
                            <div className="d-flex flex-wrap gap-1 mt-2">
                              {(p.dates || [p.weekend_date]).map((d) => (
                                <span key={d} className="badge text-bg-secondary">{dayLabel(d)}</span>
                              ))}
                            </div>
                          </div>
                          <div className="d-flex gap-1">
                            <button className="btn btn-sm btn-outline-light" onClick={() => startEdit(p)} title="Edit"><i className="bi bi-pencil" /></button>
                            <button className="btn btn-sm btn-outline-light" onClick={() => remove(p.id)} title="Delete"><i className="bi bi-trash" /></button>
                          </div>
                        </div>
                        <div className="row g-2 mt-1 small mono text-muted-2">
                          <div className="col-md-4"><i className="bi bi-unlock me-1" />{fmt(p.vote_open_at)}</div>
                          <div className="col-md-4"><i className="bi bi-megaphone me-1" />{fmt(p.publish_at)}</div>
                          <div className="col-md-4"><i className="bi bi-box-arrow-left me-1" />{fmt(p.backout_close_at)}</div>
                        </div>
                      </motion.div>
                    </StaggerItem>
                  ))}
                </Stagger>
              </AnimatePresence>
            )}
          </div></div>
        </div>
      </div>
    </>
  )
}
