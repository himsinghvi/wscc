"""Pure aggregation helpers over a list of match rows (feature 5).

Work identically on sample data and Supabase rows, since both share the match
shape: {home_team_id, away_team_id, ground_id, status, winner_id, scheduled_at}.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime


def _played(matches):
    return [m for m in matches if m.get("status") == "played"]


def head_to_head(matches) -> dict[tuple[str, str], int]:
    """Symmetric meeting counts keyed by sorted (a, b)."""
    counts: dict[tuple, int] = defaultdict(int)
    for m in matches:
        counts[tuple(sorted((m["home_team_id"], m["away_team_id"])))] += 1
    return dict(counts)


def team_record(team_id: str, matches) -> dict:
    played = won = lost = 0
    form: list[str] = []  # most-recent-first W/L
    for m in sorted(_played(matches), key=lambda x: x.get("scheduled_at", ""), reverse=True):
        if team_id not in (m["home_team_id"], m["away_team_id"]):
            continue
        played += 1
        if m.get("winner_id") == team_id:
            won += 1; form.append("W")
        else:
            lost += 1; form.append("L")
    win_pct = round(100 * won / played, 1) if played else 0.0
    return {"played": played, "won": won, "lost": lost,
            "win_pct": win_pct, "form": form[:5]}


def team_vs_all(team_id: str, teams, matches) -> list[dict]:
    out = []
    for t in teams:
        if t["id"] == team_id:
            continue
        p = w = 0
        for m in _played(matches):
            pair = {m["home_team_id"], m["away_team_id"]}
            if pair == {team_id, t["id"]}:
                p += 1
                if m.get("winner_id") == team_id:
                    w += 1
        out.append({"opponent": t["name"], "opponent_id": t["id"], "played": p, "won": w})
    return out


def standings(teams, matches) -> list[dict]:
    """Points table: 2 pts per win. Sorted by points then win%."""
    table = []
    for t in teams:
        rec = team_record(t["id"], matches)
        table.append({
            "team_id": t["id"], "team": t["name"], "short": t.get("short_name"),
            "played": rec["played"], "won": rec["won"], "lost": rec["lost"],
            "points": rec["won"] * 2, "win_pct": rec["win_pct"], "form": rec["form"],
        })
    table.sort(key=lambda r: (r["points"], r["win_pct"]), reverse=True)
    for i, r in enumerate(table, 1):
        r["position"] = i
    return table


def matches_by_month(matches) -> list[dict]:
    buckets: dict[str, int] = defaultdict(int)
    for m in _played(matches):
        try:
            dt = datetime.fromisoformat(str(m["scheduled_at"]).replace("Z", "+00:00"))
            buckets[dt.strftime("%b %Y")] += 1
        except Exception:
            continue
    # keep chronological order
    items = sorted(buckets.items(), key=lambda kv: datetime.strptime(kv[0], "%b %Y"))
    return [{"month": k.split()[0], "played": v} for k, v in items]


def ground_usage(matches, grounds) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for m in matches:
        if m.get("ground_id"):
            counts[m["ground_id"]] += 1
    gmap = {g["id"]: g["name"] for g in grounds}
    return [{"ground": gmap.get(gid, gid), "ground_id": gid, "matches": c}
            for gid, c in counts.items()]
