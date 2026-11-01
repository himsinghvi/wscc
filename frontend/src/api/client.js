import { supabase, supabaseEnabled } from '../auth/supabaseClient'

// Same-origin by default: the API lives under /api (served by FastAPI locally,
// and by a Vercel serverless function in production). Override with VITE_API_BASE_URL.
const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

// In dev mode (no Supabase) we pass the chosen demo email so the backend can
// resolve a user without a JWT. In real mode we attach the Supabase JWT.
function devEmail() {
  return localStorage.getItem('wscc_dev_email') || 'admin@wscc.app'
}

async function authHeaders() {
  if (!supabaseEnabled) return { 'X-Dev-Email': devEmail() }
  const { data } = await supabase.auth.getSession()
  const token = data?.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function api(path, { method = 'GET', body, params } = {}) {
  const headers = { 'Content-Type': 'application/json', ...(await authHeaders()) }
  let url = `${BASE}${path}`
  if (params) url += '?' + new URLSearchParams(params).toString()
  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
  return data
}

export const get = (p, params) => api(p, { params })
export const post = (p, body, params) => api(p, { method: 'POST', body, params })
export const put = (p, body, params) => api(p, { method: 'PUT', body, params })
export const del = (p, params) => api(p, { method: 'DELETE', params })
