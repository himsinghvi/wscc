import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import Footer from '../components/Footer'

// Shown while a signup request awaits admin approval (or was rejected).
export default function Pending() {
  const { me, reload, signOut } = useAuth()
  const rejected = me?.status === 'rejected'

  // poll for approval every 15s so the user auto-advances once approved
  useEffect(() => {
    if (rejected) return
    const t = setInterval(() => reload().catch(() => {}), 15000)
    return () => clearInterval(t)
  }, [rejected, reload])

  return (
    <div className="d-flex flex-column vh-100">
      <div className="flex-grow-1 d-flex align-items-center justify-content-center p-3">
        <motion.div className="card wscc p-4 p-md-5 text-center" style={{ maxWidth: 440, width: '100%' }}
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          {rejected ? (
            <>
              <i className="bi bi-x-circle-fill fs-1" style={{ color: 'var(--red)' }} />
              <h4 className="fw-bold mt-3 mb-1">Request declined</h4>
              <div className="text-muted-2 small">Your request to join {me?.team || 'the team'} wasn't approved. Please contact a league admin.</div>
            </>
          ) : (
            <>
              <motion.i className="bi bi-hourglass-split fs-1 text-primary"
                animate={{ rotate: [0, 180, 360] }} transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }} />
              <h4 className="fw-bold mt-3 mb-1">Waiting for approval</h4>
              <div className="text-muted-2 small">
                Your request to join <b>{me?.team || 'your team'}</b> is pending a league admin's approval.
                You'll get in automatically once approved.
              </div>
              <div className="text-muted-2 mt-3" style={{ fontSize: '.72rem' }}>Signed in as {me?.email}</div>
            </>
          )}
          <div className="d-flex gap-2 justify-content-center mt-4">
            {!rejected && <button className="btn btn-outline-light btn-sm" onClick={() => reload()}>
              <i className="bi bi-arrow-clockwise me-1" />Check now</button>}
            <button className="btn btn-outline-light btn-sm" onClick={signOut}><i className="bi bi-box-arrow-right me-1" />Sign out</button>
          </div>
        </motion.div>
      </div>
      <Footer />
    </div>
  )
}
