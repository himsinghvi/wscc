import AnimatedNumber from './AnimatedNumber'

const ACCENTS = {
  primary: ['rgba(91,140,255,.18)', 'var(--primary-2)'],
  violet: ['rgba(139,92,246,.18)', '#b794ff'],
  green: ['rgba(52,211,153,.16)', '#5ee6ad'],
  amber: ['rgba(251,191,36,.16)', '#ffd45e'],
  cyan: ['rgba(34,211,238,.16)', '#67e8f9'],
}

export default function StatCard({ icon, label, value, accent = 'primary', sub, animate = true }) {
  const [bg, fg] = ACCENTS[accent] || ACCENTS.primary
  const numeric = typeof value === 'number'
  return (
    <div className="card wscc h-100">
      <div className="card-body d-flex align-items-center gap-3">
        <div className="rounded-3 d-grid flex-shrink-0" style={{
          width: 50, height: 50, placeItems: 'center',
          background: bg, color: fg, fontSize: '1.35rem',
          boxShadow: `0 0 18px ${bg}`,
        }}>
          <i className={`bi bi-${icon}`} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div className="text-muted-2 small text-truncate">{label}</div>
          <div className="fs-3 fw-bold lh-1">
            {animate && numeric ? <AnimatedNumber value={value} /> : value}
          </div>
          {sub && <div className="text-muted-2" style={{ fontSize: '.7rem' }}>{sub}</div>}
        </div>
      </div>
    </div>
  )
}
