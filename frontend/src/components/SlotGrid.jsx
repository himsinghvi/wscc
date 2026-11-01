// Grid of date × slot toggles. Tokens are "YYYY-MM-DD#slot".
// tone: 'select' (green, availability) | 'backout' (red, choosing what to drop).
const dayLabel = (iso) => new Date(iso + 'T00:00').toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })

export default function SlotGrid({ dates = [], slots = [], value, onToggle, allowed, tone = 'select' }) {
  const sel = value instanceof Set ? value : new Set(value || [])
  const onClass = tone === 'backout' ? 'btn-danger' : 'btn-success'
  const onIcon = tone === 'backout' ? 'x-circle-fill' : 'check2-square'

  return (
    <div className="d-flex flex-column gap-1">
      {dates.map((d) => (
        <div key={d} className="d-flex align-items-center gap-2 flex-wrap py-1 border-bottom border-secondary-subtle">
          <div className="fw-semibold small" style={{ minWidth: 118 }}>{dayLabel(d)}</div>
          {slots.map((s) => {
            const tok = `${d}#${s}`
            const ok = !allowed || allowed.has(tok)
            const on = sel.has(tok)
            return (
              <button key={s} type="button" disabled={!ok} onClick={() => onToggle(tok)}
                className={`btn btn-sm ${on ? onClass : 'btn-outline-light'}`}
                style={{ minWidth: 66, opacity: ok ? 1 : 0.25 }}>
                <i className={`bi bi-${on ? onIcon : 'square'} me-1`} />{s}
              </button>
            )
          })}
        </div>
      ))}
    </div>
  )
}
