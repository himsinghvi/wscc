import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import Footer from '../components/Footer'

// Landing page for the password-reset email link (/reset). Supabase establishes
// a recovery session from the URL; the user sets a new password here.
export default function ResetPassword() {
  const { updatePassword } = useAuth()
  const [pw, setPw] = useState('')
  const [pw2, setPw2] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [err, setErr] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    if (pw !== pw2) { setErr('Passwords do not match.'); return }
    setBusy(true); setErr(null)
    try {
      await updatePassword(pw)
      setDone(true)
      setTimeout(() => { window.location.href = '/' }, 1500)
    } catch (e2) {
      setErr(e2.message || 'Could not update password. Open the reset link from your email again.')
    } finally { setBusy(false) }
  }

  return (
    <div className="d-flex flex-column vh-100">
      <div className="flex-grow-1 d-flex align-items-center justify-content-center p-3">
        <motion.div className="card wscc p-4 p-md-5" style={{ maxWidth: 420, width: '100%' }}
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h4 className="fw-bold mb-1 gradient-text">Set a new password</h4>
          {done ? (
            <div className="text-center py-3">
              <i className="bi bi-check-circle-fill text-success fs-1" />
              <div className="mt-2">Password updated — signing you in…</div>
            </div>
          ) : (
            <>
              <div className="text-muted-2 small mb-4">Choose a new password for your account.</div>
              <form onSubmit={submit}>
                <input type="password" className="form-control mb-2" placeholder="New password (min 6)"
                  value={pw} onChange={(e) => setPw(e.target.value)} minLength={6} required autoComplete="new-password" />
                <input type="password" className="form-control mb-3" placeholder="Confirm new password"
                  value={pw2} onChange={(e) => setPw2(e.target.value)} minLength={6} required autoComplete="new-password" />
                {err && <div className="alert alert-danger small py-2">{err}</div>}
                <button className="btn btn-primary w-100" disabled={busy || !pw}>
                  {busy ? <span className="spinner-border spinner-border-sm" /> : 'Update password'}
                </button>
              </form>
              <a href="/" className="btn btn-link btn-sm text-muted-2 mt-2 p-0">Back to sign in</a>
            </>
          )}
        </motion.div>
      </div>
      <Footer />
    </div>
  )
}
