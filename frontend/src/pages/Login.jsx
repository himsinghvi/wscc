import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import { get } from '../api/client'
import Footer from '../components/Footer'

export default function Login() {
  const { signInWithEmail, supabaseEnabled } = useAuth()
  const [email, setEmail] = useState('')
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [accounts, setAccounts] = useState([])

  useEffect(() => {
    if (!supabaseEnabled) get('/meta/test-accounts').then((d) => setAccounts(d.accounts || [])).catch(() => {})
  }, [supabaseEnabled])
  const admin = accounts.find((a) => a.role === 'admin')
  const teams = accounts.filter((a) => a.role !== 'admin')

  const submit = async (e, forced) => {
    e?.preventDefault()
    setErr(null); setMsg(null); setBusy(true)
    try {
      const r = await signInWithEmail(forced || email)
      if (r.magicLinkSent) setMsg('Check your inbox for a magic sign-in link.')
    } catch (e2) {
      setErr(e2.message || 'Sign-in failed. Is this email allow-listed?')
    } finally { setBusy(false) }
  }

  return (
    <div className="d-flex flex-column vh-100">
    <div className="flex-grow-1 d-flex align-items-center justify-content-center p-3">
      <motion.div className="card wscc p-4 p-md-5" style={{ maxWidth: 440, width: '100%' }}
        initial={{ opacity: 0, y: 24, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 0.61, 0.36, 1] }}>
        <div className="text-center mb-4">
          <motion.div className="brand-badge d-grid mx-auto mb-3" style={{ width: 60, height: 60, placeItems: 'center', fontSize: '1.6rem' }}
            animate={{ rotate: [0, -6, 6, 0] }} transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}>
            <i className="bi bi-lightning-charge-fill text-white" />
          </motion.div>
          <h4 className="fw-bold mb-1 gradient-text">Weekend Cricket League</h4>
          <div className="text-muted-2 small">Sign in with your allow-listed email</div>
        </div>

        <form onSubmit={submit}>
          <div className="mb-3">
            <label className="form-label small text-muted-2">Email</label>
            <div className="input-group">
              <span className="input-group-text bg-transparent border-secondary"><i className="bi bi-envelope text-muted-2" /></span>
              <input type="email" className="form-control form-control-lg" placeholder="you@club.com"
                value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
          </div>
          <motion.button className="btn btn-primary btn-lg w-100" disabled={busy} whileTap={{ scale: 0.97 }}>
            {busy ? <span className="spinner-border spinner-border-sm" /> :
              supabaseEnabled ? <><i className="bi bi-magic me-1" />Send magic link</> : <><i className="bi bi-box-arrow-in-right me-1" />Enter (dev mode)</>}
          </motion.button>
        </form>

        {msg && <motion.div className="alert alert-success mt-3 py-2 small mb-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>{msg}</motion.div>}
        {err && <motion.div className="alert alert-danger mt-3 py-2 small mb-0" initial={{ x: -8 }} animate={{ x: [-8, 8, -5, 5, 0] }}>{err}</motion.div>}

        {!supabaseEnabled && accounts.length > 0 && (
          <div className="mt-4">
            <div className="d-flex align-items-center justify-content-between mb-2">
              <span className="text-muted-2 small">Quick login (testing)</span>
              {admin && (
                <motion.button className="btn btn-sm btn-primary" whileTap={{ scale: 0.95 }}
                  onClick={(e) => submit(e, admin.email)} disabled={busy}>
                  <i className="bi bi-shield-lock-fill me-1" />Admin
                </motion.button>
              )}
            </div>
            <div className="text-muted-2 mb-2" style={{ fontSize: '.7rem' }}>Pick a team to sign in as its rep:</div>
            <div className="d-flex flex-wrap gap-2" style={{ maxHeight: 220, overflowY: 'auto' }}>
              {teams.map((t) => (
                <motion.button key={t.email} className="btn btn-sm btn-outline-light" whileHover={{ y: -2 }} whileTap={{ scale: 0.95 }}
                  onClick={(e) => submit(e, t.email)} disabled={busy} title={t.team}>
                  {t.team}
                </motion.button>
              ))}
            </div>
          </div>
        )}

        <div className="text-center text-muted-2 mt-4" style={{ fontSize: '.72rem' }}>
          <i className="bi bi-shield-check me-1" />Restricted to approved club emails · max 2 logins per team
        </div>
      </motion.div>
    </div>
    <Footer />
    </div>
  )
}
