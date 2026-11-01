# 🚀 Deploying WSCC

The app is **single-origin**: the API is served under `/api/*` and the React SPA
is served from the same host — so it runs on **one port** locally and on **one
domain** on Vercel.

## Run locally on ONE port

```bash
# 1) build the frontend (outputs frontend/dist)
cd frontend && npm install && npm run build

# 2) run the backend — it serves the API AND the built SPA
cd ../backend && pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8077
```

Open **http://localhost:8077** — UI + API both there:
- SPA: `http://localhost:8077/`
- API: `http://localhost:8077/api/health`

### Dev with hot-reload (two ports, optional)
Only if you want Vite HMR while developing:
```bash
cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8077
cd frontend && npm run dev     # :5173 — proxies /api → :8077
```

## Deploy to Vercel

Layout Vercel uses (already in the repo):
- `api/index.py` → Vercel **Python serverless function** exposing the FastAPI `app`
  (bundles `backend/**`).
- `frontend/` → built with **@vercel/static-build** (`npm run build` → `dist`).
- `vercel.json` routes: `/api/*` → the function, everything else → the SPA
  (`/index.html` fallback for client-side routes).

### Steps
```bash
npm i -g vercel
vercel            # first run: link/create the project
vercel --prod     # production deploy
```
Or import the repo in the Vercel dashboard — it auto-detects `vercel.json`.

### Environment variables (Vercel → Project → Settings → Environment Variables)
Set these for a real backend (leave unset to run in offline demo/dev mode):

| Variable | Scope | Notes |
|----------|-------|-------|
| `SUPABASE_URL` | backend | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | backend | **server only** |
| `SUPABASE_JWT_SECRET` | backend | to verify user JWTs |
| `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_DEPLOYMENT` | backend | optional (scheduler AI) |
| `APP_TIMEZONE` | backend | e.g. `Asia/Kolkata` |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` | build | browser auth (omit → dev mode) |

`VITE_API_BASE_URL` can stay unset — it defaults to `/api` (same origin).

### Notes
- Serverless filesystem is read-only except `/tmp`, so admin-scheduled polls and
  day-rules (which write JSON files locally) won't persist between invocations on
  Vercel — wire them to Supabase tables for durable storage. The imported league
  dataset (`backend/app/data/wscc_import.json`) is read-only and loads fine.
- With no Supabase env vars set, the deployment runs in **demo/dev mode** (the
  login page shows the test accounts). Set the Supabase vars to enable real auth + RLS.
