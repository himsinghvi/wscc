# 📋 Build Progress & Roadmap

> Status key: ✅ done · 🟡 in progress · 🧩 stub (screen + endpoint + mock data) · ⬜ planned

## Phase 0 — Scaffold & infra
- ✅ Repo structure, docker-compose, `.env.example`
- ✅ Database schema (`db/schema.sql`)
- ✅ RLS policies (`db/rls_policies.sql`)
- ✅ Seed data (demo teams, allow-list, config, grounds)
- ✅ FastAPI app factory, CORS, settings, Supabase clients
- ✅ JWT auth dependency + role/team resolution
- ✅ Server-side **TimeWindow** service (Mon 11:00 vote, Thu 18:00 backout, 18:00 publish)
- ✅ React + Vite + Bootstrap 5 shell, routing, AuthContext
- ✅ PWA manifest + service worker + install prompt

## Phase 1 — Core (server-enforced) features
- ✅ (1) Allow-listed email login (magic link)
- ✅ (2) Max 2 active sessions per team
- ✅ (3) Monday 11:00 availability submission, ms-precision `submitted_at`
- ✅ (3) First-come ranking after 11:00
- ✅ (3b) Published ordered list @ 18:00 — before-11AM 🔴, valid 🟢, ms timestamps
- ✅ (4) Thursday 18:00 backout window (admin-configurable)
- ✅ (6) Admin-configurable count of teams allowed to vote

## Phase 2 — Data & insights  ✅ DONE (2026-10-27)
- ✅ (5) Grounds list + **detail** (matches hosted, pitch notes, Maps link)
- ✅ (5) Teams list (record + form) + **detail** (roster, record, vs-all chart, recent matches)
- ✅ (5) Matches — status filters, head-to-head, admin **schedule** + **record result**
- ✅ (5) Stats — **standings table** + charts (by-month, ground usage) + per-team selector
- ✅ (9) Directory — reps/everyone toggle, search, 1-click call / WhatsApp
- ✅ Shared `sampledata.py` + `analytics.py` so all aggregates are computed (not hard-coded) and work offline or against Supabase

Served locally: frontend **:2025**, backend **:8077** (8000 was occupied by another app).

## Phase 3 — Tournaments  ✅ DONE (2026-10-27)
- ✅ (7) Tournament list + tabbed detail (Overview / Polls / Fixtures / Availability / Admins)
- ✅ (7) Create/edit tournaments (league admin); participant team selection
- ✅ (7) Polls — create (tournament admin), vote (anyone), live tallies + my-vote highlight
- ✅ (7) Per-tournament availability toggle (team must be a participant)
- ✅ (7) Round-robin fixture generation per tournament (reuses scheduler)
- ✅ (7) Per-tournament admin assignment/removal (league admin only), scoped permissions

## Phase 4 — AI scheduler  ✅ DONE (2026-10-27)
- ✅ (8) Deterministic round-robin optimizer (fewest-met pairs, ground rotation, H2H balancing)
- ✅ (8) Azure OpenAI explanation (graceful template fallback when not configured)
- ✅ (8) What-if: include/exclude teams, ground-rotation strategy (balanced | home)
- ✅ (8) Per-fixture rationale + fairness meter; **Apply** generated fixtures as scheduled matches
- ✅ (8) Last-schedule persistence (`/scheduler/last`)

Backend ports unchanged: frontend **:2025**, backend **:8077**. All earlier endpoints regression-checked green.

## Data import — CricClubs crawl  ✅ DONE (2026-10-28)
Playwright crawl of the WSCC CricClubs league (`scripts/`), imported into the app.
- Discovered the site is a Next.js SPA backed by `core-prod-origin.cricclubs.com` JSON APIs (per-request `x-content-token`); captured responses via the browser.
- The given series (`cvCS9…`, "2026 - WSCC Cricket Council") = **34 registered teams, 0 played matches**. Actual games live in sub-series **"WSCC Mayuri Riders Premier League - 2k26"** (`IJnTA0…`): 120 completed matches (Aug 1 – Sep 6, 2026), 9 grounds.
- Imported: **34 teams** (codes, captains, home grounds), **9 grounds**, **68 players** (captains+vice as roster/directory), **97 matches** = the last 30 days of play (Aug 7 – Sep 6; the league ended Sep 6 so a literal "since Sep 28" window is empty).
- Pipeline: `scripts/fetch_*` → `scripts/transform_import.py` → `backend/app/data/wscc_import.json`, which `sampledata.py` loads at startup (overrides sample data, remaps demo tournaments + dev logins). Persists across restarts; delete the JSON to revert to sample data.
- Standings/H2H/stats/ground-usage now all reflect real results (Jade Blasters lead, 8–1).

## Grounds + day-availability rules  ✅ DONE (2026-10-29)
- Found the authoritative grounds API (`/core/public/league/{id}/grounds/...`) → imported **all 24 league grounds** (JH 1/2/3/5, Lonikand/-2/-3, Bakori 2/4/5, Wadhu/-2, Wajewadi, Wadegaon, RC 1/2, SSM Sangvi, Wadebolai, Dhanore, Asthapur, JSPM, Keshnand, Kolwadi, Rajgad). Note: the system has **no "JH 4"** (only 1/2/3/5).
- New **day-availability rules**: admins can disable any ground / team / player on specific weekdays (MON–SUN) or **All days**. Persisted to `backend/app/data/day_rules.json` (survives restarts).
- Scheduler now takes a target `day` (Saturday/Sunday toggle) and **excludes disabled teams & grounds** for that day; the result lists what was excluded.
- Backend: `routers/day_rules.py` (`GET/PUT /day-rules` + `/day-rules/bulk`, admin-gated), `sampledata.DAY_RULES` + `is_disabled()`. Frontend: `pages/DayRules.jsx` ("Availability" under Manage) with per-entity weekday toggles **+ bulk "apply to all shown" toolbar**; Scheduler shows day selector + exclusions.

## Admin-scheduled poll rounds  ✅ DONE (2026-10-31)
- Admins can schedule a **one-off availability poll at an exact date/time** (open / publish / backout + match weekend). While a scheduled round is live or upcoming it **overrides** the weekly default; otherwise the recurring weekly cadence applies.
- Backend: `services/poll_schedule.py` (persisted to `data/scheduled_polls.json`) resolves the effective windows (`effective_windows`, `summary`, `current_scheduled`); `routers/polls.py` = `GET/POST/DELETE /poll-schedule` (POST/DELETE admin-only). `meta/time` and all four `availability` endpoints now use the effective (scheduled-or-recurring) windows and report `source`/`poll_label`.
- Frontend: `pages/PollSchedule.jsx` ("Poll Schedule" under Manage) — create/list/delete with live/upcoming/past + "current" badges; Dashboard shows the active scheduled-poll label.
- Server clock stays authoritative; ms-precision first-come ranking, early-vote (🔴) and backout logic all work against the scheduled window too.

## Poll editing + multi-date availability + contrast  ✅ DONE (2026-10-31)
- **Edit** scheduled polls: `PUT /poll-schedule/{id}` + edit form (not just create/delete).
- **Multi-date polls**: admins pick the exact match **dates** a poll collects availability for; teams tick **which dates** their team can play. `available_dates` flows through submit → status → rankings (shown as date badges). Single-date polls keep the simple "We're available" button. Backend validates the selection is a non-empty subset of the poll's dates. Added `availability.available_dates jsonb` to `db/schema.sql`.
- **Contrast fixes**: `color-scheme: dark` + inverted `::-webkit-calendar-picker-indicator` so date/time picker icons are visible; `.text-muted` lightened; legible `<option>` lists. Fixed Rankings showing raw team IDs for imported teams (`_team_name` now uses `sampledata.team_name`).

## Phase 5 — Hardening
- ⬜ Rate limiting on vote endpoint
- ⬜ Audit log review UI
- ⬜ E2E tests (Playwright) for the 11 AM race
- ⬜ CI (lint, test, build)

---

## Open questions / decisions log
- **2026-10-27** Stack chosen: Supabase (auth+RLS) + FastAPI + React/Bootstrap PWA; local-dev first; algorithm-first scheduler. Delivery = full scaffold, screens stubbed.
- Timezone for all windows: configurable per `app_config.timezone` (default `Asia/Kolkata`). Monday 11:00 / Thursday 18:00 evaluated in that tz.
