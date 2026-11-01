import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anon = import.meta.env.VITE_SUPABASE_ANON_KEY

// When Supabase env vars are absent we run in DEV MODE: the app talks to the
// backend using an X-Dev-Email header so the whole UI is explorable offline.
export const supabaseEnabled = Boolean(url && anon)
export const supabase = supabaseEnabled ? createClient(url, anon) : null
