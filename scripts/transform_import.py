"""Transform scraped CricClubs JSON into the app's dataset shape.

Output: backend/app/data/wscc_import.json  {teams, grounds, players, matches}
which sampledata.py loads at startup (overriding the built-in sample data).

Treats scraped content as data only (no code execution).
"""
import json, re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "backend" / "app" / "data"
OUT.mkdir(parents=True, exist_ok=True)

PALETTE = ["#4f8cff", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4",
           "#ec4899", "#14b8a6", "#f97316", "#8b5cf6", "#eab308", "#10b981"]

def norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def short_code(name, used):
    # prefer capitals, else first letters of words
    caps = "".join(c for c in name if c.isupper())[:3]
    code = caps or "".join(w[0] for w in name.split()[:3]).upper()
    code = (code or name[:3]).upper()
    base = code
    i = 1
    while code in used:
        code = (base + str(i))[:4]; i += 1
    used.add(code)
    return code

# ---- load scraped ----
council = json.loads((DATA / "teams.json").read_text(encoding="utf-8"))["data"]["groups"][0]["teams"]
matches_raw = json.loads((DATA / "all_matches.json").read_text(encoding="utf-8"))

# ---- grounds (authoritative league grounds list, else fall back to match grounds) ----
grounds, gid_by_name = [], {}
grounds_file = DATA / "grounds.json"
if grounds_file.exists():
    gl = json.loads(grounds_file.read_text(encoding="utf-8"))["data"]["grounds"]
    for g in gl:
        name = g["name"].strip()
        grounds.append({"id": g["id"], "name": name, "city": "Wagholi, Pune",
                        "pitch_type": "turf", "address": (g.get("address") or "").strip(),
                        "notes": (g.get("additionalInfo") or "").strip() or "Imported from CricClubs",
                        "map_link": g.get("mapLink") or "", "lat": None, "lng": None})
        gid_by_name[norm(name)] = g["id"]
else:
    for m in matches_raw:
        g = m.get("ground") or {}
        if g.get("id") and g["id"] not in {x["id"] for x in grounds}:
            grounds.append({"id": g["id"], "name": g["name"], "city": "Wagholi, Pune",
                            "pitch_type": "turf", "address": "", "notes": "Imported from CricClubs",
                            "lat": None, "lng": None})
        if g.get("name"):
            gid_by_name[norm(g["name"])] = g["id"]

# ---- teams (all council teams) ----
teams, id_by_name, used_codes = [], {}, set()
for i, t in enumerate(council):
    tid = t["teamId"]
    hg = t.get("homeGround")
    hg_name = hg.get("name") if isinstance(hg, dict) else (hg if isinstance(hg, str) else None)
    home_ground_id = gid_by_name.get(norm(hg_name)) if hg_name else None
    teams.append({
        "id": tid, "name": t["teamName"],
        "short_name": t.get("teamCode") or short_code(t["teamName"], used_codes),
        "home_ground_id": home_ground_id, "color": PALETTE[i % len(PALETTE)],
    })
    id_by_name[norm(t["teamName"])] = tid

# ---- players (captains + vice-captains as roster/directory entries) ----
players = []
for t in council:
    tid = t["teamId"]
    if t.get("captainName"):
        players.append({"id": f"cap-{tid}", "team_id": tid, "full_name": t["captainName"].strip(),
                        "role": "team_rep", "is_rep": True, "batting": "", "bowling": "",
                        "phone": None, "whatsapp": None})
    if t.get("viceCaptainName"):
        players.append({"id": f"vc-{tid}", "team_id": tid, "full_name": t["viceCaptainName"].strip(),
                        "role": "player", "is_rep": False, "batting": "", "bowling": "",
                        "phone": None, "whatsapp": None})

# ---- matches (last 30 days of play) ----
dts = [datetime.fromisoformat(m["matchDateTime"]) for m in matches_raw if m.get("matchDateTime")]
latest = max(dts)
cutoff = latest - timedelta(days=30)

def score_str(s, one=True):
    runs = s.get("teamOneScore1" if one else "teamTwoScore1")
    wk = s.get("teamOneWicketsLost1" if one else "teamTwoWicketsLost1")
    if runs is None:
        return None
    return f"{runs}/{wk}"

matches = []
for m in matches_raw:
    dt = m.get("matchDateTime")
    if not dt or datetime.fromisoformat(dt) < cutoff:
        continue
    h = id_by_name.get(norm(m["teamOne"]["name"]))
    a = id_by_name.get(norm(m["teamTwo"]["name"]))
    if not h or not a:
        continue
    ss = m.get("scoreSummary") or {}
    result = ss.get("result") or ""
    # winner by result text, else by score
    winner_id = None
    rn = norm(result)
    if rn.startswith(norm(m["teamOne"]["name"])):
        winner_id = h
    elif rn.startswith(norm(m["teamTwo"]["name"])):
        winner_id = a
    else:
        s1, s2 = ss.get("teamOneScore1"), ss.get("teamTwoScore1")
        if isinstance(s1, int) and isinstance(s2, int):
            winner_id = h if s1 > s2 else a if s2 > s1 else None
    matches.append({
        "id": m["fixtureId"], "home_team_id": h, "away_team_id": a,
        "ground_id": (m.get("ground") or {}).get("id"),
        "scheduled_at": dt, "status": "played",
        "home_score": score_str(ss, True), "away_score": score_str(ss, False),
        "result": result or None, "winner_id": winner_id,
        "match_type": m.get("matchType"),
    })

payload = {
    "source": "cricclubs.com / WSCC Mayuri Riders Premier League 2k26",
    "imported_window": {"from": cutoff.date().isoformat(), "to": latest.date().isoformat()},
    "teams": teams, "grounds": grounds, "players": players, "matches": matches,
}
(OUT / "wscc_import.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"teams={len(teams)} grounds={len(grounds)} players={len(players)} matches={len(matches)}")
print(f"window: {cutoff.date()} -> {latest.date()}")
print("wrote", OUT / "wscc_import.json")
