-- ============================================================
-- WSCC — Weekend Cricket League :: Schema
-- Postgres / Supabase. Run first, then rls_policies.sql, then seed.sql.
-- All timestamps are timestamptz; the server clock is authoritative.
-- ============================================================

create extension if not exists "pgcrypto";   -- gen_random_uuid()

-- ---------- enums ----------
do $$ begin
  create type user_role as enum ('player', 'team_rep', 'admin');
exception when duplicate_object then null; end $$;

do $$ begin
  create type availability_status as enum ('available', 'backed_out');
exception when duplicate_object then null; end $$;

do $$ begin
  create type session_policy as enum ('block_new', 'evict_oldest');
exception when duplicate_object then null; end $$;

-- ---------- teams ----------
create table if not exists teams (
  id            uuid primary key default gen_random_uuid(),
  name          text not null unique,
  short_name    text not null,
  logo_url      text,
  home_ground_id uuid,
  created_at    timestamptz not null default now()
);

-- ---------- allow-listed emails (feature 1) ----------
create table if not exists allowed_emails (
  email      text primary key,
  team_id    uuid references teams(id) on delete set null,
  role       user_role not null default 'player',
  is_active  boolean not null default true,
  created_at timestamptz not null default now()
);

-- ---------- players (links a Supabase auth user to a team) ----------
create table if not exists players (
  id          uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique,                 -- = auth.users.id (Supabase)
  email       text not null unique references allowed_emails(email),
  full_name   text,
  phone       text,                         -- for directory (feature 9)
  whatsapp    text,
  team_id     uuid references teams(id) on delete set null,
  role        user_role not null default 'player',
  is_rep      boolean not null default false,
  created_at  timestamptz not null default now()
);

-- ---------- active sessions (feature 2: max 2 per team) ----------
create table if not exists active_sessions (
  id          uuid primary key default gen_random_uuid(),
  player_id   uuid not null references players(id) on delete cascade,
  team_id     uuid not null references teams(id) on delete cascade,
  jti         text not null,               -- token id / session id
  user_agent  text,
  ip          inet,
  created_at  timestamptz not null default now(),
  last_seen   timestamptz not null default now(),
  revoked_at  timestamptz
);
create index if not exists idx_sessions_team_active
  on active_sessions(team_id) where revoked_at is null;

-- ---------- grounds (feature 5) ----------
create table if not exists grounds (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  address    text,
  city       text,
  lat        double precision,
  lng        double precision,
  pitch_type text,                          -- turf / matting / astro
  notes      text,
  created_at timestamptz not null default now()
);

alter table teams
  add constraint fk_teams_home_ground
  foreign key (home_ground_id) references grounds(id) on delete set null
  not valid;

-- ---------- app config (features 4 & 6, admin-tunable) ----------
create table if not exists app_config (
  id                 int primary key default 1 check (id = 1),  -- singleton
  timezone           text not null default 'Asia/Kolkata',
  vote_weekday       int  not null default 1,   -- 1=Mon (ISO)
  vote_open_time     time not null default '11:00:00',
  publish_time       time not null default '18:00:00',
  backout_weekday    int  not null default 4,   -- 4=Thu
  backout_close_time time not null default '18:00:00',
  max_voting_teams   int  not null default 0,   -- feature 6 (0 = all league teams)
  max_sessions_per_team int not null default 2, -- feature 2
  session_policy     session_policy not null default 'block_new',
  reject_early_votes boolean not null default false, -- else flag as 🔴 early
  updated_at         timestamptz not null default now(),
  updated_by         uuid references players(id)
);

-- ---------- vote cycles (one per weekend) ----------
create table if not exists vote_cycles (
  id             uuid primary key default gen_random_uuid(),
  weekend_date   date not null unique,       -- the Saturday of the weekend
  vote_open_at   timestamptz not null,       -- computed Monday 11:00 (tz-aware)
  publish_at     timestamptz not null,       -- Monday 18:00
  backout_close_at timestamptz not null,     -- Thursday 18:00
  max_voting_teams int not null,             -- snapshot of config at creation
  created_at     timestamptz not null default now()
);

-- ---------- availability submissions (features 3, 3b, 4) ----------
create table if not exists availability (
  id           uuid primary key default gen_random_uuid(),
  cycle_id     uuid not null references vote_cycles(id) on delete cascade,
  team_id      uuid not null references teams(id) on delete cascade,
  submitted_by uuid not null references players(id),
  submitted_at timestamptz not null default clock_timestamp(), -- ms precision, server clock
  status       availability_status not null default 'available',
  is_early     boolean not null default false,   -- voted before vote_open_at → 🔴
  rank         int,                              -- first-come rank, filled at publish
  available_dates jsonb,                          -- polled dates the team can play (derived)
  available_slots jsonb,                           -- "date#slot" tokens the team can play
  backed_out_slots jsonb,                          -- "date#slot" tokens backed out of
  backed_out_at timestamptz,
  backed_out_by uuid references players(id),
  note         text,
  unique (cycle_id, team_id)                      -- one submission per team per cycle
);
create index if not exists idx_avail_cycle_order
  on availability(cycle_id, submitted_at);

-- ---------- matches (feature 5 & scheduler output) ----------
create table if not exists matches (
  id          uuid primary key default gen_random_uuid(),
  cycle_id    uuid references vote_cycles(id) on delete set null,
  tournament_id uuid,
  home_team_id uuid not null references teams(id),
  away_team_id uuid not null references teams(id),
  ground_id   uuid references grounds(id),
  scheduled_at timestamptz,
  status      text not null default 'scheduled', -- scheduled|played|cancelled
  home_score  text,
  away_score  text,
  result      text,                               -- e.g. "home won by 20 runs"
  created_at  timestamptz not null default now(),
  check (home_team_id <> away_team_id)
);
create index if not exists idx_matches_teams on matches(home_team_id, away_team_id);

-- ---------- tournaments (feature 7) ----------
create table if not exists tournaments (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  description text,
  start_date  date,
  end_date    date,
  format      text,                               -- league / knockout / mixed
  created_by  uuid references players(id),
  created_at  timestamptz not null default now()
);

create table if not exists tournament_admins (
  tournament_id uuid not null references tournaments(id) on delete cascade,
  player_id     uuid not null references players(id) on delete cascade,
  assigned_by   uuid references players(id),
  assigned_at   timestamptz not null default now(),
  primary key (tournament_id, player_id)
);

create table if not exists tournament_polls (
  id            uuid primary key default gen_random_uuid(),
  tournament_id uuid not null references tournaments(id) on delete cascade,
  question      text not null,
  options       jsonb not null default '[]',
  closes_at     timestamptz,
  created_at    timestamptz not null default now()
);

create table if not exists tournament_poll_votes (
  poll_id    uuid not null references tournament_polls(id) on delete cascade,
  player_id  uuid not null references players(id) on delete cascade,
  option_idx int not null,
  voted_at   timestamptz not null default clock_timestamp(),
  primary key (poll_id, player_id)
);

-- ---------- admin-scheduled poll rounds (durable, replaces JSON file) ----------
create table if not exists scheduled_polls (
  id               uuid primary key default gen_random_uuid(),
  label            text,
  weekend_date     date,
  dates            jsonb not null default '[]',   -- polled match dates (iso)
  slots            jsonb not null default '[]',   -- slot labels per day
  vote_open_at     timestamptz not null,
  publish_at       timestamptz not null,
  backout_close_at timestamptz not null,
  created_by       uuid references players(id),
  created_at       timestamptz not null default now()
);

-- ---------- day-availability rules (durable, replaces JSON file) ----------
create table if not exists day_rules (
  entity_type text not null check (entity_type in ('ground','team','player')),
  entity_id   text not null,
  days        jsonb not null default '[]',        -- ['MON'..'SUN'] or ['ANY']
  updated_at  timestamptz not null default now(),
  primary key (entity_type, entity_id)
);

-- ---------- signup requests (team-select + admin approval) ----------
create table if not exists signup_requests (
  email       text primary key,
  team_id     uuid references teams(id) on delete set null,
  full_name   text,
  status      text not null default 'pending' check (status in ('pending','approved','rejected')),
  created_at  timestamptz not null default now(),
  decided_by  uuid references players(id),
  decided_at  timestamptz
);

-- ---------- audit log (admin/config changes) ----------
create table if not exists audit_log (
  id         bigint generated always as identity primary key,
  actor_id   uuid references players(id),
  action     text not null,
  entity     text,
  entity_id  text,
  detail     jsonb,
  at         timestamptz not null default now()
);

-- ---------- helper: current player row from JWT ----------
create or replace function current_player()
returns players language sql stable as $$
  select * from players where auth_user_id = auth.uid() limit 1;
$$;

create or replace function current_role_is(target user_role)
returns boolean language sql stable as $$
  select exists(select 1 from players where auth_user_id = auth.uid() and role = target);
$$;
