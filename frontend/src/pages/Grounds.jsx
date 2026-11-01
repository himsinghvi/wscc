import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { get } from '../api/client'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import GroundFormModal from '../components/GroundFormModal'
import { Stagger, StaggerItem } from '../components/motion'

export default function Grounds() {
  const { me } = useAuth()
  const [grounds, setGrounds] = useState([])
  const [adding, setAdding] = useState(false)
  const nav = useNavigate()

  const load = useCallback(() => { get('/grounds').then((d) => setGrounds(d.grounds)).catch(() => {}) }, [])
  useEffect(() => { load() }, [load])

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-1">
        <h3 className="fw-bold mb-0">Grounds</h3>
        {me?.is_admin && (
          <button className="btn btn-primary btn-sm" onClick={() => setAdding(true)}>
            <i className="bi bi-plus-lg me-1" /> Add ground
          </button>
        )}
      </div>
      <div className="text-muted-2 small mb-4">Tap a ground for details and matches hosted.</div>
      <Stagger className="row g-3">
        {grounds.map((g) => (
          <StaggerItem className="col-md-6 col-lg-4" key={g.id}>
            <motion.button className="card wscc h-100 w-100 border-0 text-start" onClick={() => nav(`/grounds/${g.id}`)}
              whileHover={{ y: -5 }} whileTap={{ scale: 0.98 }}>
              <div className="card-body">
                <div className="d-flex align-items-center gap-2 mb-2">
                  <i className="bi bi-geo-alt-fill text-primary fs-4" />
                  <h6 className="mb-0">{g.name}</h6>
                </div>
                <div className="text-muted-2 small">{g.city}</div>
                <div className="d-flex gap-2 mt-2">
                  <span className="badge text-bg-secondary text-capitalize">{g.pitch_type}</span>
                  <span className="badge text-bg-primary">{g.match_count} matches</span>
                </div>
              </div>
            </motion.button>
          </StaggerItem>
        ))}
      </Stagger>

      {adding && <GroundFormModal onClose={() => setAdding(false)} onDone={() => { setAdding(false); load() }} />}
    </>
  )
}
