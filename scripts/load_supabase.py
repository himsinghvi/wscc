"""Load the imported CricClubs dataset into the Supabase Postgres DB.

Maps CricClubs string ids -> deterministic UUIDs (uuid5), applies a small
idempotent migration, clears prior sports data (keeps config/allow-list), then
inserts grounds -> teams -> players -> matches. Runs via the Management API."""
import json, os, uuid, urllib.request, pathlib

PAT = os.environ["PAT"]; REF = os.environ["REF"]
NS = uuid.uuid5(uuid.NAMESPACE_DNS, "wscc.cricclubs")
U = lambda cid: str(uuid.uuid5(NS, cid)) if cid else None
Q = lambda s: "'" + str(s).replace("'", "''") + "'" if s is not None else "NULL"

data = json.loads((pathlib.Path(__file__).resolve().parent.parent /
                   "backend/app/data/wscc_import.json").read_text(encoding="utf-8"))

sql = ["""
alter table teams   add column if not exists color text;
alter table matches add column if not exists winner_id uuid references teams(id);
alter table matches add column if not exists match_type text;
alter table players alter column email drop not null;
delete from matches; delete from players; delete from teams; delete from grounds;
"""]

for g in data["grounds"]:
    sql.append(f"insert into grounds(id,name,city,pitch_type,address,notes,lat,lng) values "
               f"({Q(U(g['id']))},{Q(g['name'])},{Q(g.get('city'))},{Q(g.get('pitch_type'))},"
               f"{Q(g.get('address'))},{Q(g.get('notes'))},"
               f"{g.get('lat') if g.get('lat') is not None else 'NULL'},"
               f"{g.get('lng') if g.get('lng') is not None else 'NULL'});")

for t in data["teams"]:
    sql.append(f"insert into teams(id,name,short_name,home_ground_id,color) values "
               f"({Q(U(t['id']))},{Q(t['name'])},{Q(t['short_name'])},"
               f"{Q(U(t.get('home_ground_id')))},{Q(t.get('color'))});")

for p in data.get("players", []):
    sql.append(f"insert into players(id,full_name,phone,whatsapp,team_id,role,is_rep) values "
               f"({Q(U(p['id']))},{Q(p['full_name'])},{Q(p.get('phone'))},{Q(p.get('whatsapp'))},"
               f"{Q(U(p['team_id']))},{Q(p.get('role','player'))},{str(bool(p.get('is_rep'))).lower()});")

for m in data["matches"]:
    sql.append(f"insert into matches(id,home_team_id,away_team_id,ground_id,scheduled_at,status,"
               f"home_score,away_score,result,winner_id,match_type) values "
               f"({Q(U(m['id']))},{Q(U(m['home_team_id']))},{Q(U(m['away_team_id']))},"
               f"{Q(U(m.get('ground_id')))},{Q(m.get('scheduled_at'))},{Q(m.get('status','played'))},"
               f"{Q(m.get('home_score'))},{Q(m.get('away_score'))},{Q(m.get('result'))},"
               f"{Q(U(m.get('winner_id')))},{Q(m.get('match_type'))});")

sql.append("select (select count(*) from teams) teams,(select count(*) from grounds) grounds,"
           "(select count(*) from players) players,(select count(*) from matches) matches;")

body = json.dumps({"query": "\n".join(sql)}).encode()
req = urllib.request.Request(f"https://api.supabase.com/v1/projects/{REF}/database/query",
    data=body, headers={"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"}, method="POST")
try:
    print("RESULT:", urllib.request.urlopen(req, timeout=120).read().decode())
except urllib.error.HTTPError as e:
    print("ERROR", e.code, e.read().decode()[:800])
