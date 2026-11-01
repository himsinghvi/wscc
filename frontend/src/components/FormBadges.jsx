// Renders recent W/L form as coloured pills (most-recent first).
export default function FormBadges({ form = [], empty = '—' }) {
  if (!form.length) return <span className="text-muted-2 small">{empty}</span>
  return (
    <span className="d-inline-flex gap-1">
      {form.map((r, i) => (
        <span key={i} className="badge rounded-circle d-grid"
          style={{
            width: 22, height: 22, placeItems: 'center', padding: 0,
            background: r === 'W' ? 'rgba(34,197,94,.2)' : 'rgba(239,68,68,.2)',
            color: r === 'W' ? '#86efac' : '#fca5a5',
          }} title={r === 'W' ? 'Win' : 'Loss'}>{r}</span>
      ))}
    </span>
  )
}
