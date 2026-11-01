-- ============================================================
-- WSCC :: Seed / demo data
-- ============================================================

-- singleton config
insert into app_config (id) values (1)
on conflict (id) do nothing;

-- grounds
insert into grounds (id, name, city, pitch_type) values
  ('11111111-1111-1111-1111-111111111111', 'Riverside Oval',   'Pune',   'turf'),
  ('22222222-2222-2222-2222-222222222222', 'Hillview Ground',  'Pune',   'matting'),
  ('33333333-3333-3333-3333-333333333333', 'Central Astro Park','Mumbai','astro')
on conflict do nothing;

-- teams
insert into teams (id, name, short_name, home_ground_id) values
  ('aaaaaaaa-0000-0000-0000-000000000001', 'Royal Strikers',   'RS', '11111111-1111-1111-1111-111111111111'),
  ('aaaaaaaa-0000-0000-0000-000000000002', 'Thunder Kings',    'TK', '22222222-2222-2222-2222-222222222222'),
  ('aaaaaaaa-0000-0000-0000-000000000003', 'Coastal Chargers', 'CC', '33333333-3333-3333-3333-333333333333'),
  ('aaaaaaaa-0000-0000-0000-000000000004', 'Valley Vipers',    'VV', null),
  ('aaaaaaaa-0000-0000-0000-000000000005', 'Metro Mavericks',  'MM', null),
  ('aaaaaaaa-0000-0000-0000-000000000006', 'Summit Smashers',  'SS', null)
on conflict do nothing;

-- allow-listed emails (feature 1) — 2 per team (feature 2 cap)
insert into allowed_emails (email, team_id, role) values
  ('admin@wscc.app',    'aaaaaaaa-0000-0000-0000-000000000001', 'admin'),
  ('rep.rs@wscc.app',   'aaaaaaaa-0000-0000-0000-000000000001', 'team_rep'),
  ('rep.tk@wscc.app',   'aaaaaaaa-0000-0000-0000-000000000002', 'team_rep'),
  ('player.tk@wscc.app','aaaaaaaa-0000-0000-0000-000000000002', 'player'),
  ('rep.cc@wscc.app',   'aaaaaaaa-0000-0000-0000-000000000003', 'team_rep'),
  ('rep.vv@wscc.app',   'aaaaaaaa-0000-0000-0000-000000000004', 'team_rep'),
  ('rep.mm@wscc.app',   'aaaaaaaa-0000-0000-0000-000000000005', 'team_rep'),
  ('rep.ss@wscc.app',   'aaaaaaaa-0000-0000-0000-000000000006', 'team_rep')
on conflict (email) do nothing;

-- demo players (auth_user_id gets linked on first real sign-in)
insert into players (email, full_name, phone, whatsapp, team_id, role, is_rep) values
  ('admin@wscc.app',    'League Admin',   '+919000000000', '+919000000000', 'aaaaaaaa-0000-0000-0000-000000000001', 'admin',   true),
  ('rep.rs@wscc.app',   'Ravi (RS Rep)',  '+919000000001', '+919000000001', 'aaaaaaaa-0000-0000-0000-000000000001', 'team_rep',true),
  ('rep.tk@wscc.app',   'Tarun (TK Rep)', '+919000000002', '+919000000002', 'aaaaaaaa-0000-0000-0000-000000000002', 'team_rep',true),
  ('rep.cc@wscc.app',   'Chetan (CC Rep)','+919000000003', '+919000000003', 'aaaaaaaa-0000-0000-0000-000000000003', 'team_rep',true)
on conflict (email) do nothing;

-- a couple of historical matches for head-to-head demo
insert into matches (home_team_id, away_team_id, ground_id, scheduled_at, status, home_score, away_score, result) values
  ('aaaaaaaa-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000002','11111111-1111-1111-1111-111111111111', now() - interval '21 days', 'played', '156/6', '150/9', 'Royal Strikers won by 6 runs'),
  ('aaaaaaaa-0000-0000-0000-000000000003','aaaaaaaa-0000-0000-0000-000000000001','33333333-3333-3333-3333-333333333333', now() - interval '14 days', 'played', '132/8', '133/4', 'Royal Strikers won by 6 wkts')
on conflict do nothing;
