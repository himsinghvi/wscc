import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { get } from '../api/client'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import FormBadges from '../components/FormBadges'
import TeamFormModal from '../components/TeamFormModal'
import { Stagger, StaggerItem } from '../components/motion'

export default function Teams() {
  const { me } = useAuth()
  const [teams, setTeams] = useState([])
  const [adding, setAdding] = useState(false)
  const nav = useNavigate()

  const load = useCallback(() => { get('/teams').then((d) => setTeams(d.teams)).catch(() => {}) }, [])
  useEffect(() => { load() }, [load])

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-1">
        <h3 className="fw-bold mb-0">Teams</h3>
        {me?.is_admin && (
          <button className="btn btn-primary btn-sm" onClick={() => setAdding(true)}>
            <i className="bi bi-plus-lg me-1" /> Add team
          </button>
        )}
      </div>
      <div className="text-muted-2 small mb-4">Tap a team for roster, record and head-to-head.</div>
      <Stagger className="row g-3">
        {teams.map((t) => (
          <StaggerItem className="col-6 col-md-4 col-lg-3" key={t.id}>
            <motion.button className="card wscc h-100 w-100 border-0 text-start" onClick={() => nav(`/teams/${t.id}`)}
              whileHover={{ y: -5 }} whileTap={{ scale: 0.98 }}>
              <div className="card-body">
                <div className="d-flex align-items-center gap-2 mb-2">
                  <div className="rounded-circle d-grid" style={{
                    width: 46, height: 46, placeItems: 'center', fontWeight: 700,
                    background: (t.color || '#4f8cff') + '33', color: t.color || '#4f8cff',
                    boxShadow: `0 0 16px ${(t.color || '#4f8cff')}44`,
                  }}>{t.short_name}</div>
                  <div>
                    <div className="fw-semibold lh-1">{t.name}</div>
                    <div className="text-muted-2" style={{ fontSize: '.72rem' }}>
                      {t.record?.played ?? 0} played · {t.record?.win_pct ?? 0}% won
                    </div>
                  </div>
                </div>
                <FormBadges form={t.record?.form} />
              </div>
            </motion.button>
          </StaggerItem>
        ))}
      </Stagger>

      {adding && <TeamFormModal onClose={() => setAdding(false)} onDone={() => { setAdding(false); load() }} />}
    </>
  )
}
