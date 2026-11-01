import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { get, put } from '../api/client'
import { Stagger, StaggerItem } from '../components/motion'

const TABS = [
  { key: 'ground', label: 'Grounds', icon: 'geo-alt-fill' },
  { key: 'team', label: 'Teams', icon: 'people-fill' },
  { key: 'player', label: 'Players', icon: 'person-fill' },
]

export default function DayRules() {
  const [tab, setTab] = useState('ground')
  const [weekdays, setWeekdays] = useState([])
  const [rules, setRules] = useState({ ground: {}, team: {}, player: {} })
  const [entities, setEntities] = useState({ ground: [], team: [], player: [] })
  const [q, setQ] = useState('')
  const [saving, setSaving] = useState(null)

  const loadRules = useCallback(() => get('/day-rules').then((d) => {
    setWeekdays(d.weekdays); setRules(d.rules)
  }).catch(() => {}), [])

  useEffect(() => {
    loadRules()
    get('/grounds').then((d) => setEntities((e) => ({ ...e, ground: d.grounds.map((g) => ({ id: g.id, name: g.name, sub: g.city })) }))).catch(() => {})
    get('/teams').then((d) => setEntities((e) => ({ ...e, team: d.teams.map((t) => ({ id: t.id, name: t.name, sub: t.short_name })) }))).catch(() => {})
    get('/directory', { reps_only: false }).then((d) => setEntities((e) => ({ ...e, player: d.directory.map((p) => ({ id: p.player_id, name: p.name, sub: p.team })) }))).catch(() => {})
  }, [loadRules])

  const daysFor = (type, id) => rules[type]?.[id] || []

  const toggle = async (type, id, day) => {
    const cur = new Set(daysFor(type, id))
    if (day === 'ANY') { cur.has('ANY') ? cur.delete('ANY') : (cur.clear(), cur.add('ANY')) }
    else { cur.delete('ANY'); cur.has(day) ? cur.delete(day) : cur.add(day) }
    const days = [...cur]
    setSaving(`${type}:${id}`)
    try {
      const r = await put('/day-rules', { entity_type: type, entity_id: id, days })
      setRules((prev) => {
        const next = { ...prev, [type]: { ...prev[type] } }
        if (r.days.length) next[type][id] = r.days; else delete next[type][id]
        return next
      })
    } finally { setSaving(null) }
  }

  const list = (entities[tab] || []).filter((e) => e.id && (!q || e.name.toLowerCase().includes(q.toLowerCase())))
  const disabledCount = Object.keys(rules[tab] || {}).length

  // bulk apply the computed per-entity day lists to all shown entities
  const bulkApply = async (build) => {
    if (!list.length) return
    setSaving('bulk')
    try {
      const items = list.map((e) => ({ entity_id: e.id, days: build(new Set(daysFor(tab, e.id))) }))
      const r = await put('/day-rules/bulk', { entity_type: tab, items })
      setRules((prev) => ({ ...prev, [tab]: r.rules }))
    } finally { setSaving(null) }
  }
  const allHaveDay = (d) => list.length > 0 && list.every((e) => daysFor(tab, e.id).includes(d))
  const allAny = allHaveDay('ANY')
  const toggleAllDay = (d) => {
    const remove = allHaveDay(d)
    bulkApply((cur) => { cur.delete('ANY'); remove ? cur.delete(d) : cur.add(d); return [...cur] })
  }
  const toggleAllAny = () => bulkApply(() => (allAny ? [] : ['ANY']))
  const clearAll = () => bulkApply(() => [])

  return (
    <>
      <h3 className="fw-bold mb-1">Availability rules</h3>
      <div className="text-muted-2 small mb-3">
        Temporarily disable a ground, team or player for specific weekdays. Disabled entities are
        excluded by the AI scheduler for that day. <b>All days</b> disables it entirely.
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3">
        {TABS.map((t) => {
          const n = Object.keys(rules[t.key] || {}).length
          return (
            <button key={t.key} className={`btn btn-sm ${tab === t.key ? 'btn-primary' : 'btn-outline-light'}`} onClick={() => setTab(t.key)}>
              <i className={`bi bi-${t.icon} me-1`} />{t.label}
              {n > 0 && <span className="badge text-bg-danger ms-2">{n}</span>}
            </button>
          )
        })}
      </div>

      <div className="mb-3" style={{ maxWidth: 340 }}>
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-transparent border-secondary"><i className="bi bi-search text-muted-2" /></span>
          <input className="form-control" placeholder={`Search ${tab}s`} value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      {/* bulk "apply to all shown" toolbar */}
      <div className="card wscc mb-3"><div className="card-body py-2 d-flex align-items-center gap-2 flex-wrap">
        <span className="small text-muted-2 me-1">
          <i className="bi bi-lightning-charge-fill me-1" />Apply to all {list.length} shown{q ? ' (filtered)' : ''}:
        </span>
        {weekdays.map((d) => (
          <button key={d} disabled={saving === 'bulk' || !list.length} onClick={() => toggleAllDay(d)}
            className={`btn btn-sm ${allHaveDay(d) ? 'btn-danger' : 'btn-outline-light'}`} style={{ minWidth: 42 }}>
            {d[0] + d.slice(1).toLowerCase()}
          </button>
        ))}
        <span className="vr mx-1 d-none d-sm-inline" />
        <button disabled={saving === 'bulk' || !list.length} onClick={toggleAllAny}
          className={`btn btn-sm ${allAny ? 'btn-danger' : 'btn-outline-light'}`}>All days</button>
        <button disabled={saving === 'bulk' || !list.length} onClick={clearAll} className="btn btn-sm btn-outline-light">
          <i className="bi bi-x-circle me-1" />Clear all
        </button>
        {saving === 'bulk' && <span className="spinner-border spinner-border-sm text-primary" />}
      </div></div>

      <AnimatePresence mode="wait">
        <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
          <Stagger className="d-flex flex-column gap-2">
            {list.map((e) => {
              const days = daysFor(tab, e.id)
              const off = days.length > 0
              return (
                <StaggerItem key={e.id}>
                  <div className="card wscc">
                    <div className="card-body py-2 d-flex align-items-center justify-content-between flex-wrap gap-2">
                      <div style={{ minWidth: 160 }}>
                        <div className="fw-semibold">
                          {e.name}
                          {off && <span className="badge text-bg-danger ms-2">{days.includes('ANY') ? 'disabled' : days.join(', ')}</span>}
                        </div>
                        {e.sub && <div className="text-muted-2" style={{ fontSize: '.72rem' }}>{e.sub}</div>}
                      </div>
                      <div className="d-flex gap-1 flex-wrap align-items-center">
                        {weekdays.map((d) => {
                          const on = days.includes(d)
                          const weekend = d === 'SAT' || d === 'SUN'
                          return (
                            <button key={d} onClick={() => toggle(tab, e.id, d)} disabled={saving === `${tab}:${e.id}`}
                              className={`btn btn-sm ${on ? 'btn-danger' : 'btn-outline-light'}`}
                              style={{ minWidth: 42, opacity: weekend || on ? 1 : 0.7 }} title={weekend ? 'Weekend' : ''}>
                              {d[0] + d.slice(1).toLowerCase()}
                            </button>
                          )
                        })}
                        <span className="vr mx-1" />
                        <button onClick={() => toggle(tab, e.id, 'ANY')} disabled={saving === `${tab}:${e.id}`}
                          className={`btn btn-sm ${days.includes('ANY') ? 'btn-danger' : 'btn-outline-light'}`}>All days</button>
                      </div>
                    </div>
                  </div>
                </StaggerItem>
              )
            })}
          </Stagger>
          {list.length === 0 && <div className="text-muted-2 small">No {tab}s.</div>}
        </motion.div>
      </AnimatePresence>

      <div className="text-muted-2 small mt-3">
        <i className="bi bi-info-circle me-1" />{disabledCount} {tab}{disabledCount === 1 ? '' : 's'} currently have day rules.
        Rules persist across restarts.
      </div>
    </>
  )
}
