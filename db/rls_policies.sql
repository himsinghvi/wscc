-- ============================================================
-- WSCC :: Row-Level Security policies (defense-in-depth)
-- The FastAPI backend uses the service-role key and enforces the
-- real business logic. These policies protect direct/anon access
-- (e.g. Supabase client in the browser) so a client can never read
-- or write outside its lane even if an endpoint had a bug.
-- ============================================================

alter table teams                  enable row level security;
alter table allowed_emails         enable row level security;
alter table players                enable row level security;
alter table active_sessions        enable row level security;
alter table grounds                enable row level security;
alter table app_config             enable row level security;
alter table vote_cycles            enable row level security;
alter table availability           enable row level security;
alter table matches                enable row level security;
alter table tournaments            enable row level security;
alter table tournament_admins      enable row level security;
alter table tournament_polls       enable row level security;
alter table tournament_poll_votes  enable row level security;
alter table scheduled_polls        enable row level security;
alter table day_rules              enable row level security;
alter table audit_log              enable row level security;

-- Convenience: service role bypasses RLS automatically in Supabase.
-- Policies below target the authenticated (anon→user) client.

-- ---- Reference/read-mostly data: any authenticated user can read ----
create policy teams_read   on teams            for select to authenticated using (true);
create policy grounds_read on grounds          for select to authenticated using (true);
create policy config_read  on app_config       for select to authenticated using (true);
create policy cycles_read  on vote_cycles      for select to authenticated using (true);
create policy matches_read on matches          for select to authenticated using (true);
create policy tourn_read   on tournaments      for select to authenticated using (true);
create policy polls_read   on tournament_polls for select to authenticated using (true);

-- ---- players: read all (directory), edit only your own row ----
create policy players_read on players for select to authenticated using (true);
create policy players_self_update on players for update to authenticated
  using (auth_user_id = auth.uid())
  with check (auth_user_id = auth.uid());

-- ---- allowed_emails: admin only ----
create policy allowed_admin_all on allowed_emails for all to authenticated
  using (current_role_is('admin')) with check (current_role_is('admin'));

-- ---- active_sessions: a player sees only their own ----
create policy sessions_self on active_sessions for select to authenticated
  using (player_id = (select id from players where auth_user_id = auth.uid()));

-- ---- availability ----
-- Read: your own team's rows always; everyone's rows only AFTER publish time.
create policy avail_read on availability for select to authenticated using (
  team_id = (select team_id from players where auth_user_id = auth.uid())
  or exists (
      select 1 from vote_cycles c
      where c.id = availability.cycle_id and now() >= c.publish_at
  )
  or current_role_is('admin')
);
-- Direct writes are blocked for clients; the backend (service role) performs
-- the server-clock-stamped insert. No insert/update policy for `authenticated`.

-- ---- app_config: only admins may change (backend also guards) ----
create policy config_admin_write on app_config for all to authenticated
  using (current_role_is('admin')) with check (current_role_is('admin'));

-- ---- tournaments: admins + assigned tournament admins may write ----
create policy tourn_write on tournaments for all to authenticated
  using (
    current_role_is('admin')
    or exists (select 1 from tournament_admins ta
               join players p on p.id = ta.player_id
               where ta.tournament_id = tournaments.id and p.auth_user_id = auth.uid())
  ) with check (
    current_role_is('admin')
    or exists (select 1 from tournament_admins ta
               join players p on p.id = ta.player_id
               where ta.tournament_id = tournaments.id and p.auth_user_id = auth.uid())
  );

create policy tourn_admins_manage on tournament_admins for all to authenticated
  using (current_role_is('admin')) with check (current_role_is('admin'));

-- ---- poll votes: a player manages only their own vote ----
create policy pollvote_self on tournament_poll_votes for all to authenticated
  using (player_id = (select id from players where auth_user_id = auth.uid()))
  with check (player_id = (select id from players where auth_user_id = auth.uid()));

-- ---- scheduled_polls + day_rules: everyone reads, admins write ----
create policy sched_read on scheduled_polls for select to authenticated using (true);
create policy sched_admin on scheduled_polls for all to authenticated
  using (current_role_is('admin')) with check (current_role_is('admin'));

create policy dayrules_read on day_rules for select to authenticated using (true);
create policy dayrules_admin on day_rules for all to authenticated
  using (current_role_is('admin')) with check (current_role_is('admin'));

-- ---- audit_log: admins read; nobody writes directly ----
create policy audit_admin_read on audit_log for select to authenticated
  using (current_role_is('admin'));
