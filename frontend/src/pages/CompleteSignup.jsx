import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import { get, post } from '../api/client'
import Footer from '../components/Footer'

// Shown when a user is signed in but hasn't yet requested to join a team.
export default function CompleteSignup() {
  const { me, reload, signOut } = useAuth()
  const [teams, setTeams] = useState([])
  const [teamId, setTeamId] = useState('')
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  useEffect(() => { get('/meta/teams-public').then((d) => setTeams(d.teams)).catch(() => {}) }, [])

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr(null)
    try {
      await post('/signup/request', { team_id: teamId, full_name: name || null })
      await reload()   // → status becomes 'pending'
    } catch (e2) { setErr(e2.message || 'Could not submit request.') } finally { setBusy(false) }
  }

  return (
    <div className="d-flex flex-column vh-100">
      <div className="flex-grow-1 d-flex align-items-center justify-content-center p-3">
        <motion.div className="card wscc p-4 p-md-5" style={{ maxWidth: 440, width: '100%' }}
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h4 className="fw-bold mb-1 gradient-text">Almost there</h4>
          <div className="text-muted-2 small mb-4">Pick your team to request access, {me?.email}.</div>
          <form onSubmit={submit}>
            <label className="form-label small text-muted-2">Your name (optional)</label>
            <input className="form-control mb-3" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Himanshu Singhvi" />
            <label className="form-label small text-muted-2">Team</label>
            <select className="form-select mb-3" value={teamId} onChange={(e) => setTeamId(e.target.value)} required>
              <option value="">— select your team —</option>
              {teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
            {err && <div className="alert alert-danger small py-2">{err}</div>}
            <button className="btn btn-primary w-100" disabled={busy || !teamId}>
              {busy ? <span className="spinner-border spinner-border-sm" /> : 'Request to join'}
            </button>
          </form>
          <div className="text-muted-2 mt-3" style={{ fontSize: '.72rem' }}>
            <i className="bi bi-info-circle me-1" />An admin will approve your request. Max 2 members per team.
          </div>
          <button className="btn btn-link btn-sm text-muted-2 mt-2 p-0" onClick={signOut}>Sign out</button>
        </motion.div>
      </div>
      <Footer />
    </div>
  )
}
