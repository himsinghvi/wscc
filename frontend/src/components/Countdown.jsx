import { useEffect, useState } from 'react'

// Renders a live countdown to a target ISO timestamp. Purely cosmetic — the
// backend remains the source of truth for whether an action is actually allowed.
export default function Countdown({ to, label }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])

  const target = new Date(to).getTime()
  let diff = Math.max(0, target - now)
  const d = Math.floor(diff / 86400000); diff -= d * 86400000
  const h = Math.floor(diff / 3600000); diff -= h * 3600000
  const m = Math.floor(diff / 60000); diff -= m * 60000
  const s = Math.floor(diff / 1000)
  const parts = [d && `${d}d`, `${String(h).padStart(2, '0')}h`,
    `${String(m).padStart(2, '0')}m`, `${String(s).padStart(2, '0')}s`].filter(Boolean)

  return (
    <span className="mono">
      {label && <span className="text-muted-2 me-1">{label}</span>}
      {parts.join(' ')}
    </span>
  )
}
