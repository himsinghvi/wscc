import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import { get } from '../api/client'
import Footer from '../components/Footer'

export default function Login() {
  const { signInWithEmail, signInWithPassword, signUpWithPassword, supabaseEnabled } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('signin')   // 'signin' | 'signup'
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [accounts, setAccounts] = useState([])

  useEffect(() => {
    if (!supabaseEnabled) get('/meta/test-accounts').then((d) => setAccounts(d.accounts || [])).catch(() => {})
  }, [supabaseEnabled])
  const admin = accounts.find((a) => a.role === 'admin')
  const teams = accounts.filter((a) => a.role !== 'admin')

  // dev-mode quick login (unchanged): email only
  const devLogin = async (e, forced) => {
    e?.preventDefault(); setErr(null); setMsg(null); setBusy(true)
    try { await signInWithEmail(forced || email) }
    catch (e2) { setErr(e2.message || 'Sign-in failed.') } finally { setBusy(false) }
  }

  const submit = async (e) => {
    e?.preventDefault()
    if (!supabaseEnabled) return devLogin(e)
    setErr(null); setMsg(null); setBusy(true)
    try {
      if (mode === 'signup') {
        const r = await signUpWithPassword(email, password)
        if (r.needsConfirm) setMsg('Account created — check your email to confirm, then sign in.')
      } else {
        await signInWithPassword(email, password)
      }
    } catch (e2) {
      setErr(e2.message || 'Sign-in failed. Check your email/password or sign up first.')
    } finally { setBusy(false) }
  }

  const magicLink = async () => {
    setErr(null); setMsg(null); setBusy(true)
    try { await signInWithEmail(email); setMsg('Magic link sent — check your inbox.') }
    catch (e2) { setErr(e2.message) } finally { setBusy(false) }
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
          <div className="text-muted-2 small">
            {supabaseEnabled ? (mode === 'signup' ? 'Create your account' : 'Sign in to your account') : 'Sign in (dev mode)'}
          </div>
        </div>

        <form onSubmit={submit}>
          <label className="form-label small text-muted-2">Email</label>
          <div className="input-group mb-3">
            <span className="input-group-text bg-transparent border-secondary"><i className="bi bi-envelope text-muted-2" /></span>
            <input type="email" className="form-control form-control-lg" placeholder="you@club.com"
              value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          </div>

          {supabaseEnabled && (
            <>
              <label className="form-label small text-muted-2">Password</label>
              <div className="input-group mb-3">
                <span className="input-group-text bg-transparent border-secondary"><i className="bi bi-lock text-muted-2" /></span>
                <input type="password" className="form-control form-control-lg" placeholder="••••••••"
                  value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6}
                  autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} />
              </div>
            </>
          )}

          <motion.button className="btn btn-primary btn-lg w-100" disabled={busy} whileTap={{ scale: 0.97 }}>
            {busy ? <span className="spinner-border spinner-border-sm" /> :
              !supabaseEnabled ? <><i className="bi bi-box-arrow-in-right me-1" />Enter (dev mode)</> :
              mode === 'signup' ? <><i className="bi bi-person-plus me-1" />Create account</> :
              <><i className="bi bi-box-arrow-in-right me-1" />Sign in</>}
          </motion.button>
        </form>

        {supabaseEnabled && (
          <div className="d-flex justify-content-between mt-3" style={{ fontSize: '.8rem' }}>
            <button className="btn btn-link p-0 text-decoration-none" style={{ fontSize: '.8rem' }}
              onClick={() => { setMode(mode === 'signup' ? 'signin' : 'signup'); setErr(null); setMsg(null) }}>
              {mode === 'signup' ? 'Have an account? Sign in' : 'First time? Create account'}
            </button>
            <button className="btn btn-link p-0 text-decoration-none text-muted-2" style={{ fontSize: '.8rem' }}
              onClick={magicLink} disabled={busy || !email}>Email me a link instead</button>
          </div>
        )}

        {msg && <motion.div className="alert alert-success mt-3 py-2 small mb-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>{msg}</motion.div>}
        {err && <motion.div className="alert alert-danger mt-3 py-2 small mb-0" initial={{ x: -8 }} animate={{ x: [-8, 8, -5, 5, 0] }}>{err}</motion.div>}

        {!supabaseEnabled && accounts.length > 0 && (
          <div className="mt-4">
            <div className="d-flex align-items-center justify-content-between mb-2">
              <span className="text-muted-2 small">Quick login (testing)</span>
              {admin && (
                <motion.button className="btn btn-sm btn-primary" whileTap={{ scale: 0.95 }}
                  onClick={(e) => devLogin(e, admin.email)} disabled={busy}>
                  <i className="bi bi-shield-lock-fill me-1" />Admin
                </motion.button>
              )}
            </div>
            <div className="text-muted-2 mb-2" style={{ fontSize: '.7rem' }}>Pick a team to sign in as its rep:</div>
            <div className="d-flex flex-wrap gap-2" style={{ maxHeight: 220, overflowY: 'auto' }}>
              {teams.map((t) => (
                <motion.button key={t.email} className="btn btn-sm btn-outline-light" whileHover={{ y: -2 }} whileTap={{ scale: 0.95 }}
                  onClick={(e) => devLogin(e, t.email)} disabled={busy} title={t.team}>
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
