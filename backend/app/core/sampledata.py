"""Shared sample dataset for offline/dev mode (features 5 & 9).

Single source of truth so teams/grounds/matches/players stay consistent across
routers. In Supabase mode the routers query the DB instead; the analytics
helpers in services/analytics.py operate on the same row shape either way.
"""
from datetime import datetime, timedelta, timezone

RS = "aaaaaaaa-0000-0000-0000-000000000001"
TK = "aaaaaaaa-0000-0000-0000-000000000002"
CC = "aaaaaaaa-0000-0000-0000-000000000003"
VV = "aaaaaaaa-0000-0000-0000-000000000004"
MM = "aaaaaaaa-0000-0000-0000-000000000005"
SS = "aaaaaaaa-0000-0000-0000-000000000006"

G1 = "11111111-1111-1111-1111-111111111111"
G2 = "22222222-2222-2222-2222-222222222222"
G3 = "33333333-3333-3333-3333-333333333333"

TEAMS = [
    {"id": RS, "name": "Royal Strikers", "short_name": "RS", "home_ground_id": G1, "color": "#4f8cff"},
    {"id": TK, "name": "Thunder Kings", "short_name": "TK", "home_ground_id": G2, "color": "#f59e0b"},
    {"id": CC, "name": "Coastal Chargers", "short_name": "CC", "home_ground_id": G3, "color": "#22c55e"},
    {"id": VV, "name": "Valley Vipers", "short_name": "VV", "home_ground_id": None, "color": "#a855f7"},
    {"id": MM, "name": "Metro Mavericks", "short_name": "MM", "home_ground_id": None, "color": "#06b6d4"},
    {"id": SS, "name": "Summit Smashers", "short_name": "SS", "home_ground_id": None, "color": "#ef4444"},
]

GROUNDS = [
    {"id": G1, "name": "Riverside Oval", "city": "Pune", "pitch_type": "turf",
     "address": "Riverside Rd, Pune", "lat": 18.5204, "lng": 73.8567,
     "notes": "True bounce, favours batters. Short square boundaries."},
    {"id": G2, "name": "Hillview Ground", "city": "Pune", "pitch_type": "matting",
     "address": "Hill Rd, Pune", "lat": 18.5308, "lng": 73.8475,
     "notes": "Low & slow. Spinners come into play in the second innings."},
    {"id": G3, "name": "Central Astro Park", "city": "Mumbai", "pitch_type": "astro",
     "address": "Central Ave, Mumbai", "lat": 19.0760, "lng": 72.8777,
     "notes": "Quick outfield, consistent carry. Great for a high-scoring game."},
]

# Rosters (feature 5 — team detail). Phones reused for the directory (feature 9).
PLAYERS = [
    {"id": "p-rs-1", "team_id": RS, "full_name": "Ravi Shah", "role": "player", "is_rep": True,  "batting": "RHB", "bowling": "RM",  "phone": "+919000000001", "whatsapp": "+919000000001"},
    {"id": "p-rs-2", "team_id": RS, "full_name": "Arjun Rao", "role": "player", "is_rep": False, "batting": "LHB", "bowling": "OB",  "phone": "+919000000011", "whatsapp": "+919000000011"},
    {"id": "p-rs-3", "team_id": RS, "full_name": "Neel Kapoor","role": "player", "is_rep": False, "batting": "RHB", "bowling": "LB",  "phone": "+919000000012", "whatsapp": "+919000000012"},
    {"id": "p-tk-1", "team_id": TK, "full_name": "Tarun Iyer", "role": "player", "is_rep": True,  "batting": "RHB", "bowling": "RFM", "phone": "+919000000002", "whatsapp": "+919000000002"},
    {"id": "p-tk-2", "team_id": TK, "full_name": "Sahil Mehta","role": "player", "is_rep": False, "batting": "LHB", "bowling": "SLA", "phone": "+919000000021", "whatsapp": "+919000000021"},
    {"id": "p-cc-1", "team_id": CC, "full_name": "Chetan Nair", "role": "player", "is_rep": True,  "batting": "RHB", "bowling": "RM",  "phone": "+919000000003", "whatsapp": "+919000000003"},
    {"id": "p-cc-2", "team_id": CC, "full_name": "Vikram Das",  "role": "player", "is_rep": False, "batting": "RHB", "bowling": "OB",  "phone": "+919000000031", "whatsapp": "+919000000031"},
    {"id": "p-vv-1", "team_id": VV, "full_name": "Imran Sheikh","role": "player", "is_rep": True,  "batting": "LHB", "bowling": "LFM", "phone": "+919000000004", "whatsapp": "+919000000004"},
    {"id": "p-mm-1", "team_id": MM, "full_name": "Rohit Verma", "role": "player", "is_rep": True,  "batting": "RHB", "bowling": "LB",  "phone": "+919000000005", "whatsapp": "+919000000005"},
    {"id": "p-ss-1", "team_id": SS, "full_name": "Kabir Khanna","role": "player", "is_rep": True,  "batting": "RHB", "bowling": "RM",  "phone": "+919000000006", "whatsapp": "+919000000006"},
]

_now = datetime.now(timezone.utc)


def _d(days_ago: int) -> str:
    return (_now - timedelta(days=days_ago)).isoformat()


def _fwd(days: int) -> str:
    return (_now + timedelta(days=days)).isoformat()


# Mix of played (with scores/result) and scheduled matches across all teams.
MATCHES = [
    {"id": "m01", "home_team_id": RS, "away_team_id": TK, "ground_id": G1, "scheduled_at": _d(42), "status": "played", "home_score": "156/6", "away_score": "150/9", "result": "Royal Strikers won by 6 runs", "winner_id": RS},
    {"id": "m02", "home_team_id": CC, "away_team_id": RS, "ground_id": G3, "scheduled_at": _d(35), "status": "played", "home_score": "132/8", "away_score": "133/4", "result": "Royal Strikers won by 6 wkts", "winner_id": RS},
    {"id": "m03", "home_team_id": TK, "away_team_id": CC, "ground_id": G2, "scheduled_at": _d(28), "status": "played", "home_score": "168/5", "away_score": "140/10", "result": "Thunder Kings won by 28 runs", "winner_id": TK},
    {"id": "m04", "home_team_id": VV, "away_team_id": MM, "ground_id": G1, "scheduled_at": _d(28), "status": "played", "home_score": "121/9", "away_score": "122/7", "result": "Metro Mavericks won by 3 wkts", "winner_id": MM},
    {"id": "m05", "home_team_id": SS, "away_team_id": RS, "ground_id": G2, "scheduled_at": _d(21), "status": "played", "home_score": "145/7", "away_score": "149/5", "result": "Royal Strikers won by 5 wkts", "winner_id": RS},
    {"id": "m06", "home_team_id": TK, "away_team_id": VV, "ground_id": G3, "scheduled_at": _d(21), "status": "played", "home_score": "177/4", "away_score": "159/8", "result": "Thunder Kings won by 18 runs", "winner_id": TK},
    {"id": "m07", "home_team_id": CC, "away_team_id": MM, "ground_id": G3, "scheduled_at": _d(14), "status": "played", "home_score": "138/10","away_score": "139/6", "result": "Metro Mavericks won by 4 wkts", "winner_id": MM},
    {"id": "m08", "home_team_id": RS, "away_team_id": VV, "ground_id": G1, "scheduled_at": _d(14), "status": "played", "home_score": "162/5", "away_score": "118/10","result": "Royal Strikers won by 44 runs", "winner_id": RS},
    {"id": "m09", "home_team_id": SS, "away_team_id": TK, "ground_id": G2, "scheduled_at": _d(7),  "status": "played", "home_score": "151/8", "away_score": "152/3", "result": "Thunder Kings won by 7 wkts", "winner_id": TK},
    {"id": "m10", "home_team_id": MM, "away_team_id": SS, "ground_id": G1, "scheduled_at": _d(7),  "status": "played", "home_score": "144/6", "away_score": "143/9", "result": "Metro Mavericks won by 1 run", "winner_id": MM},
    {"id": "m11", "home_team_id": RS, "away_team_id": MM, "ground_id": G1, "scheduled_at": _fwd(3), "status": "scheduled"},
    {"id": "m12", "home_team_id": TK, "away_team_id": SS, "ground_id": G2, "scheduled_at": _fwd(3), "status": "scheduled"},
    {"id": "m13", "home_team_id": CC, "away_team_id": VV, "ground_id": G3, "scheduled_at": _fwd(4), "status": "scheduled"},
]

TEAMS_BY_ID = {t["id"]: t for t in TEAMS}
GROUNDS_BY_ID = {g["id"]: g for g in GROUNDS}


def team_name(tid: str) -> str:
    return TEAMS_BY_ID.get(tid, {}).get("name", tid)


def ground_name(gid) -> str:
    return GROUNDS_BY_ID.get(gid, {}).get("name") if gid else None


# ============================================================
# Tournaments (feature 7). Dev-mode state lives here; Supabase
# mode uses the tournaments / tournament_* tables instead.
# ============================================================
TOURNAMENTS = [
    {
        "id": "t1", "name": "Monsoon Cup 2026", "format": "league",
        "description": "Six-team single round robin followed by a top-two final. "
                       "Played across all three grounds over six weekends.",
        "start_date": "2026-11-07", "end_date": "2026-12-20", "status": "upcoming",
        "team_ids": [RS, TK, CC, VV, MM, SS],
        "admin_player_ids": ["dev-rs"],          # league admin is always implicitly an admin
    },
    {
        "id": "t2", "name": "Summer Smash (T10)", "format": "knockout",
        "description": "Fast T10 knockout. Eight slots, straight elimination.",
        "start_date": "2027-03-14", "end_date": "2027-03-28", "status": "draft",
        "team_ids": [RS, TK, CC, VV],
        "admin_player_ids": [],
    },
]

# polls: list of {id, tournament_id, question, options[], closes_at}
TOURNAMENT_POLLS = [
    {"id": "pl1", "tournament_id": "t1", "question": "Preferred venue for the final?",
     "options": ["Riverside Oval", "Central Astro Park", "Hillview Ground"], "closes_at": _fwd(20)},
    {"id": "pl2", "tournament_id": "t1", "question": "Overs per innings?",
     "options": ["T20 (20 overs)", "T15 (15 overs)"], "closes_at": _fwd(10)},
]

# in-memory mutable stores (dev mode only)
POLL_VOTES: dict[str, dict[str, int]] = {        # poll_id -> {player_id: option_idx}
    "pl1": {"dev-rs": 0, "dev-tk": 1, "dev-cc": 0, "dev-vv": 1, "dev-mm": 0},
    "pl2": {"dev-rs": 0, "dev-tk": 0, "dev-cc": 1},
}
TOURN_AVAIL: dict[str, dict[str, dict]] = {       # tournament_id -> {team_id: {available, at}}
    "t1": {RS: {"available": True}, TK: {"available": True}, CC: {"available": True}},
}
TOURNAMENT_FIXTURES: dict[str, list] = {"t1": [], "t2": []}   # tournament_id -> [fixture rows]

TOURNAMENTS_BY_ID = {t["id"]: t for t in TOURNAMENTS}


# ============================================================
# Optional real dataset imported from CricClubs (scripts/transform_import.py).
# When present it REPLACES the built-in sample teams/grounds/players/matches,
# and the demo tournaments + dev logins are remapped onto the imported teams so
# every screen stays coherent. Falls back silently to the sample data.
# ============================================================
import json as _json
from pathlib import Path as _Path

IMPORT_META: dict = {}


def _apply_import():
    global TEAMS, GROUNDS, PLAYERS, MATCHES, TEAMS_BY_ID, GROUNDS_BY_ID, IMPORT_META
    path = _Path(__file__).resolve().parent.parent / "data" / "wscc_import.json"
    if not path.exists():
        return
    try:
        d = _json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not d.get("teams"):
        return

    TEAMS = d["teams"]
    GROUNDS = d["grounds"]
    PLAYERS = d.get("players", [])
    MATCHES = d["matches"]
    TEAMS_BY_ID = {t["id"]: t for t in TEAMS}
    GROUNDS_BY_ID = {g["id"]: g for g in GROUNDS}
    IMPORT_META = {"source": d.get("source"), "window": d.get("imported_window"),
                   "teams": len(TEAMS), "grounds": len(GROUNDS), "matches": len(MATCHES)}

    # Remap demo tournaments onto imported teams so chips/fixtures stay coherent.
    ids = [t["id"] for t in TEAMS]
    if ids:
        for t, n in zip(TOURNAMENTS, (min(8, len(ids)), min(4, len(ids)))):
            t["team_ids"] = ids[:n]
        TOURN_AVAIL.clear()
        TOURN_AVAIL["t1"] = {i: {"available": True} for i in ids[:3]}
        for k in list(TOURNAMENT_FIXTURES):
            TOURNAMENT_FIXTURES[k] = []

    # Dev logins are derived live from TEAMS (see dev_accounts), so no remap needed.


_apply_import()


# ============================================================
# Day-availability rules (temporary disables for scheduling).
# An entity (ground / team / player) can be disabled on specific weekdays
# ("MON".."SUN") or "ANY" (every day). Disabled entities are excluded by the
# scheduler for that day. Persisted to data/day_rules.json.
# ============================================================
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
ENTITY_TYPES = ("ground", "team", "player")
_DAY_RULES_PATH = _Path(__file__).resolve().parent.parent / "data" / "day_rules.json"

DAY_RULES: dict[str, dict[str, list[str]]] = {t: {} for t in ENTITY_TYPES}


def weekday_code(d) -> str:
    """date/datetime -> 'MON'..'SUN'."""
    return WEEKDAYS[d.weekday()]


def day_rules_map() -> dict:
    """Full {entity_type: {entity_id: [days]}} — from Supabase when configured,
    else the in-memory/JSON dev store. Fetch once and pass to is_disabled()."""
    from .supabase_client import service_client
    sb = service_client()
    if sb is None:
        return {t: {k: list(v) for k, v in DAY_RULES.get(t, {}).items()} for t in ENTITY_TYPES}
    out = {t: {} for t in ENTITY_TYPES}
    try:
        for r in (sb.table("day_rules").select("*").execute().data or []):
            out.setdefault(r["entity_type"], {})[r["entity_id"]] = r.get("days") or []
    except Exception:
        pass
    return out


def is_disabled(entity_type: str, entity_id: str, day: str, rules: dict | None = None) -> bool:
    rules = rules if rules is not None else day_rules_map()
    r = rules.get(entity_type, {}).get(entity_id) or []
    return "ANY" in r or day in r


def _save_day_rules():
    try:
        _DAY_RULES_PATH.write_text(_json.dumps(DAY_RULES, indent=2), encoding="utf-8")
    except Exception:
        pass


def set_day_rule(entity_type: str, entity_id: str, days):
    if entity_type not in ENTITY_TYPES:
        raise ValueError("bad entity_type")
    valid = sorted({d for d in (days or []) if d in WEEKDAYS or d == "ANY"})
    from .supabase_client import service_client
    sb = service_client()
    if sb is None:
        if valid:
            DAY_RULES.setdefault(entity_type, {})[entity_id] = valid
        else:
            DAY_RULES.get(entity_type, {}).pop(entity_id, None)
        _save_day_rules()
    elif valid:
        sb.table("day_rules").upsert(
            {"entity_type": entity_type, "entity_id": entity_id, "days": valid}).execute()
    else:
        sb.table("day_rules").delete().eq("entity_type", entity_type).eq("entity_id", entity_id).execute()
    return valid


def _load_day_rules():
    if _DAY_RULES_PATH.exists():
        try:
            data = _json.loads(_DAY_RULES_PATH.read_text(encoding="utf-8"))
            for t in ENTITY_TYPES:
                DAY_RULES[t] = {k: list(v) for k, v in (data.get(t) or {}).items()}
        except Exception:
            pass


_load_day_rules()


# ============================================================
# Dev-mode test accounts (offline only). One admin + one rep per team, derived
# from the current teams so they always map to real team ids. Used by the login
# page's quick-login buttons and by auth._lookup_player.
# ============================================================
def dev_accounts(n: int = 12) -> list[dict]:
    accts = [{"email": "admin@wscc.app", "label": "Admin", "team": "League Admin",
              "team_id": TEAMS[0]["id"] if TEAMS else None, "player_id": "dev-admin",
              "role": "admin"}]
    for i, t in enumerate(TEAMS[:n]):
        accts.append({"email": f"team{i + 1}@wscc.test", "label": t["short_name"],
                      "team": t["name"], "team_id": t["id"],
                      "player_id": f"dev-{t['id']}", "role": "team_rep"})
    return accts


def dev_account_for(email: str) -> dict | None:
    el = (email or "").strip().lower()
    return next((a for a in dev_accounts(99) if a["email"].lower() == el), None)
