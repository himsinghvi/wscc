import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { supabase, supabaseEnabled } from './supabaseClient'
import { get, post } from '../api/client'

const AuthCtx = createContext(null)
export const useAuth = () => useContext(AuthCtx)

// Stable per-device/tab session id used for the "max 2 logins per team" check.
function sessionJti() {
  let j = localStorage.getItem('wscc_jti')
  if (!j) { j = crypto.randomUUID(); localStorage.setItem('wscc_jti', j) }
  return j
}

export function AuthProvider({ children }) {
  const [me, setMe] = useState(null)
  const [loading, setLoading] = useState(true)
  const [session, setSession] = useState(null)

  const loadMe = useCallback(async () => {
    try {
      const profile = await get('/meta/me')
      setMe(profile)
      // register session (server enforces the 2-per-team cap)
      await post('/sessions/register', { jti: sessionJti(), user_agent: navigator.userAgent })
        .catch((e) => { throw e })
    } catch (e) {
      setMe(null)
      throw e
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!supabaseEnabled) { loadMe().catch(() => {}); return }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      if (data.session) loadMe().catch(() => {}); else setLoading(false)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_e, s) => {
      setSession(s)
      if (s) loadMe().catch(() => {}); else { setMe(null); setLoading(false) }
    })
    return () => sub.subscription.unsubscribe()
  }, [loadMe])

  const signInWithEmail = async (email) => {
    if (!supabaseEnabled) {
      localStorage.setItem('wscc_dev_email', email)
      setLoading(true)
      await loadMe()
      return { dev: true }
    }
    const { error } = await supabase.auth.signInWithOtp({ email })
    if (error) throw error
    return { magicLinkSent: true }
  }

  const signInWithPassword = async (email, password) => {
    if (!supabaseEnabled) { localStorage.setItem('wscc_dev_email', email); setLoading(true); await loadMe(); return { dev: true } }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    return { ok: true }
  }

  const signUpWithPassword = async (email, password) => {
    if (!supabaseEnabled) { localStorage.setItem('wscc_dev_email', email); setLoading(true); await loadMe(); return { dev: true } }
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
    // instant-confirm is on, so a session is returned and we're signed in
    if (!data.session) return { needsConfirm: true }
    return { ok: true }
  }

  const signOut = async () => {
    await post('/sessions/logout', { jti: sessionJti() }).catch(() => {})
    if (supabaseEnabled) await supabase.auth.signOut()
    else localStorage.removeItem('wscc_dev_email')
    setMe(null)
  }

  return (
    <AuthCtx.Provider value={{ me, loading, session, supabaseEnabled, signInWithEmail, signInWithPassword, signUpWithPassword, signOut, reload: loadMe }}>
      {children}
    </AuthCtx.Provider>
  )
}
