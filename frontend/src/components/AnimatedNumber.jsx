import { useEffect, useRef, useState } from 'react'
import { animate } from 'framer-motion'

// Counts up to `value` on mount / when value changes. Non-numeric values
// (e.g. "3/8") render as-is.
export default function AnimatedNumber({ value, duration = 1 }) {
  const numeric = typeof value === 'number' && isFinite(value)
  const [display, setDisplay] = useState(numeric ? 0 : value)
  const node = useRef(null)

  useEffect(() => {
    if (!numeric) { setDisplay(value); return }
    const controls = animate(0, value, {
      duration,
      ease: [0.22, 0.61, 0.36, 1],
      onUpdate: (v) => setDisplay(Math.round(v)),
    })
    return () => controls.stop()
  }, [value, numeric, duration])

  return <span ref={node}>{display}</span>
}
