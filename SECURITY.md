# 🔐 Security & Trust Model

Guiding principle: **the client is untrusted.** Every rule that affects fairness, timing, or access is decided by the FastAPI backend using the **server clock** and the authenticated identity, then backstopped by Postgres Row-Level Security. The React app only renders server-provided state and disables controls for UX — it never grants permission.

## Identity
- Auth via **Supabase Auth** (magic-link / OTP) restricted to an **allow-list** (`allowed_emails`). Sign-in for any non-allow-listed email is rejected server-side even if Supabase issues a token.
- The browser holds only a short-lived Supabase **user JWT**. FastAPI verifies the JWT signature (JWKS) on every request and resolves `user_id → player → team → role`.

## Enforcement matrix (never trusted to the frontend)

| Rule | Where enforced | How |
|------|----------------|-----|
| Email must be allow-listed | Backend + RLS + DB trigger | `allowed_emails` check on first sign-in |
| Max **2 active logins per team** | Backend | Active-session table; 3rd session rejected / oldest revoked per policy |
| Availability only **after Mon 11:00:00.000** | Backend (server clock) | `TimeWindow.vote_open_at`; `submitted_at` set server-side with ms precision |
| **First-come** ordering | Backend/DB | `submitted_at timestamptz` + monotonic tiebreak; ordering computed in SQL |
| Published list visible **only after 18:00 Mon** | Backend + RLS | `TimeWindow.publish_at` gate |
| Backout only **before Thu 18:00** | Backend (server clock) | `TimeWindow.backout_close_at` |
| **N teams** allowed to vote | Backend | `app_config.max_voting_teams`; enforced at submit |
| Admin-only actions | Backend + RLS | `role in ('admin')`; tournament admin scoped by `tournament_admins` |
| Writes to others' rows | RLS | Policies keyed on `auth.uid()` / team / role |

## Anti-manipulation notes
- **Clock spoofing:** client-supplied timestamps are ignored; `submitted_at = now()` in the DB/`server`.
- **Replay/double-vote:** unique constraint `(cycle_id, team_id)` on submissions; upsert controlled by window state.
- **Early vote (before 11:00):** accepted but flagged `is_early=true` → shown 🔴 and excluded from the valid first-come ranking. (Alternatively hard-reject; configurable via `app_config.reject_early_votes`.)
- **Session cap bypass:** session registry is server-owned; logging in from a 3rd device triggers policy (`block_new` or `evict_oldest`).
- **RLS as backstop:** even if an endpoint had a bug, Postgres policies prevent cross-team/cross-tenant reads/writes.

## Secrets
- `SUPABASE_SERVICE_ROLE_KEY`, `AZURE_OPENAI_API_KEY` live only in the backend env, never shipped to the browser. Frontend gets only `SUPABASE_URL` + `SUPABASE_ANON_KEY`.

## TODO (hardening backlog)
- Per-IP + per-user rate limit on `/availability/submit`.
- Signed audit log (append-only) for all admin/config changes.
- Playwright test simulating the 11:00:00 stampede for correct ordering.
