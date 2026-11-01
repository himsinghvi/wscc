import { useState } from 'react'

// Inline month calendar that lets the user pick MULTIPLE dates by clicking.
// value: array of 'YYYY-MM-DD'; onChange: (nextArray) => void
const WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const iso = (y, m, d) => `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`

export default function MultiDateCalendar({ value = [], onChange }) {
  const today = new Date()
  const first = value.length ? new Date(value[0] + 'T00:00') : today
  const [view, setView] = useState({ y: first.getFullYear(), m: first.getMonth() })
  const sel = new Set(value)

  const y = view.y, m = view.m
  const monthName = new Date(y, m, 1).toLocaleDateString([], { month: 'long', year: 'numeric' })
  const daysInMonth = new Date(y, m + 1, 0).getDate()
  // Monday-first offset for the 1st of the month
  const lead = (new Date(y, m, 1).getDay() + 6) % 7
  const todayIso = iso(today.getFullYear(), today.getMonth(), today.getDate())

  const move = (delta) => {
    const d = new Date(y, m + delta, 1)
    setView({ y: d.getFullYear(), m: d.getMonth() })
  }
  const toggle = (d) => {
    const key = iso(y, m, d)
    const next = new Set(sel)
    next.has(key) ? next.delete(key) : next.add(key)
    onChange([...next].sort())
  }

  const cells = []
  for (let i = 0; i < lead; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)

  return (
    <div className="rounded-3 p-2" style={{ background: 'rgba(7,12,24,.5)', border: '1px solid var(--border-soft)' }}>
      <div className="d-flex align-items-center justify-content-between mb-2 px-1">
        <button type="button" className="btn btn-sm btn-outline-light border-0" onClick={() => move(-1)}><i className="bi bi-chevron-left" /></button>
        <span className="fw-semibold small">{monthName}</span>
        <button type="button" className="btn btn-sm btn-outline-light border-0" onClick={() => move(1)}><i className="bi bi-chevron-right" /></button>
      </div>
      <div className="d-grid" style={{ gridTemplateColumns: 'repeat(7,1fr)', gap: 4 }}>
        {WD.map((w) => (
          <div key={w} className="text-center text-muted-2" style={{ fontSize: '.64rem', fontWeight: 600 }}>{w}</div>
        ))}
        {cells.map((d, i) => {
          if (!d) return <div key={`e${i}`} />
          const key = iso(y, m, d)
          const on = sel.has(key)
          const isToday = key === todayIso
          const weekend = [5, 6].includes((new Date(y, m, d).getDay() + 6) % 7)
          return (
            <button key={key} type="button" onClick={() => toggle(d)}
              className="btn btn-sm p-0 d-flex align-items-center justify-content-center"
              style={{
                height: 40, minWidth: 0, borderRadius: 9, fontSize: '.85rem', lineHeight: 1,
                touchAction: 'manipulation',
                border: isToday ? '1px solid var(--primary)' : '1px solid transparent',
                background: on ? 'linear-gradient(135deg,var(--primary),var(--accent))' : 'transparent',
                color: on ? '#fff' : weekend ? 'var(--primary-2)' : 'var(--text)',
                fontWeight: on ? 700 : 500,
              }}>
              {d}
            </button>
          )
        })}
      </div>
    </div>
  )
}
