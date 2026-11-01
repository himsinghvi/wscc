"""AI/statistical round-robin scheduler endpoint (feature 8).

Deterministic fairness-first pairing (fewest-met pairs first, grounds rotated),
with Azure OpenAI used to explain the result. Supports what-if team selection
and applying the generated fixtures as real scheduled matches.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core.supabase_client import service_client
from ..core.time_windows import current_cycle_windows, now as tz_now
from ..core import sampledata as S
from ..schemas import ScheduleRequest, ApplyScheduleRequest
from ..services.config_service import window_config
from ..services.poll_schedule import effective_windows
from ..services.scheduler import build_round_robin
from ..services.ai import explain_schedule
from . import availability as avail_router

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# Last generated schedule, kept so the UI can review then apply it.
_LAST: dict = {}


def _teams(sb):
    return S.TEAMS if sb is None else sb.table("teams").select("id,name,home_ground_id").execute().data


def _matches(sb):
    return S.MATCHES if sb is None else sb.table("matches").select("home_team_id,away_team_id").execute().data


def _grounds(sb):
    return ([g["id"] for g in S.GROUNDS] if sb is None
            else [g["id"] for g in sb.table("grounds").select("id").execute().data])


def _head_to_head(sb) -> dict:
    counts: dict[tuple, int] = {}
    for m in _matches(sb):
        key = tuple(sorted((m["home_team_id"], m["away_team_id"])))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _reason(p, rotation: str) -> str:
    bits = []
    if p.meetings_so_far == 0:
        bits.append("never met before")
    else:
        bits.append(f"only met {p.meetings_so_far}×")
    bits.append("neutral/rotated ground" if rotation == "balanced" else "home advantage")
    return "; ".join(bits)


def _respondents(sb, w):
    """Teams that submitted availability (and haven't fully backed out)."""
    rows = avail_router._current_rows(sb, w.weekend_date.isoformat())
    return [r for r in rows if r.get("status") != "backed_out"]


def _all_matches(sb):
    return S.MATCHES if sb is None else sb.table("matches").select("*").execute().data


def _weekend_context(sb, poll_dates):
    """From matches already scheduled on the poll's dates, build (avoid_pairs,
    team_grounds) so the generator never repeats an opponent or ground."""
    dates = set(poll_dates or [])
    avoid_pairs, team_grounds = set(), {}
    for m in _all_matches(sb):
        d = str(m.get("scheduled_at") or "")[:10]
        if d not in dates:
            continue
        a, b = m.get("home_team_id"), m.get("away_team_id")
        if a and b:
            avoid_pairs.add(tuple(sorted((a, b))))
        g = m.get("ground_id")
        if g:
            team_grounds.setdefault(a, set()).add(g)
            team_grounds.setdefault(b, set()).add(g)
    return avoid_pairs, team_grounds


def _validate_fixtures(fixtures, existing_pairs, existing_grounds):
    """A team must not get the same opponent or the same ground twice this
    weekend (across the submitted set + already-scheduled matches)."""
    pairs = set(existing_pairs)
    tg = {t: set(g) for t, g in existing_grounds.items()}
    errors = []
    for f in fixtures:
        a, b, g = f.get("home_team_id"), f.get("away_team_id"), f.get("ground_id")
        if not a or not b:
            errors.append("A fixture is missing a team."); continue
        if a == b:
            errors.append("A team cannot play itself."); continue
        key = tuple(sorted((a, b)))
        if key in pairs:
            errors.append(f"{S.team_name(a)} vs {S.team_name(b)} is scheduled more than once.")
        pairs.add(key)
        if g:
            for t in (a, b):
                if g in tg.get(t, set()):
                    errors.append(f"{S.team_name(t)} is assigned {S.ground_name(g)} more than once.")
                tg.setdefault(t, set()).add(g)
    return errors


@router.get("/eligible")
def eligible(user: CurrentUser = Depends(require_admin)):
    """Teams that have responded to the current poll — the only ones the
    scheduler considers (request #2)."""
    cfg = window_config()
    w, meta = effective_windows(cfg, tz_now(cfg))
    sb = service_client()
    rows = _respondents(sb, w)
    teams = [{"id": r["team_id"], "name": S.team_name(r["team_id"]),
              "short": S.TEAMS_BY_ID.get(r["team_id"], {}).get("short_name"),
              "available_dates": r.get("available_dates"),
              "available_slots": r.get("available_slots")} for r in rows]
    return {"weekend_date": w.weekend_date.isoformat(), "poll_label": meta["label"],
            "dates": meta.get("dates"), "slots": meta.get("slots"),
            "teams": teams, "count": len(teams)}


@router.post("/generate")
def generate(body: ScheduleRequest, user: CurrentUser = Depends(require_admin)):
    from datetime import date as _date
    cfg = window_config()
    w, meta = effective_windows(cfg, tz_now(cfg))
    sb = service_client()

    teams = _teams(sb)
    team_names = {t["id"]: t["name"] for t in teams}
    home_ground = {t["id"]: t.get("home_ground_id") for t in teams}

    # Target match date: a date from the schedule (not a fixed Sat/Sun).
    poll_dates = meta.get("dates") or [w.weekend_date.isoformat()]
    target_date = body.date if (body.date in poll_dates) else poll_dates[0]
    day = S.weekday_code(_date.fromisoformat(target_date))

    # Only teams that responded AND are available on the target date (request #2 + #3).
    def avail_on(r):
        if r.get("available_dates"):
            return target_date in r["available_dates"]
        return True  # no per-date info → treat as available
    respondent_ids = [r["team_id"] for r in _respondents(sb, w) if avail_on(r)]
    if body.team_ids:
        team_ids = [t for t in body.team_ids if t in respondent_ids] or list(body.team_ids)
    else:
        team_ids = respondent_ids
    if body.exclude_team_ids:
        team_ids = [t for t in team_ids if t not in set(body.exclude_team_ids)]

    # Day-availability rules: drop teams/grounds disabled on the target weekday.
    rules = S.day_rules_map()
    excluded_teams = [t for t in team_ids if S.is_disabled("team", t, day, rules)]
    team_ids = [t for t in team_ids if t not in set(excluded_teams)]

    if len(team_ids) < 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Need at least two available teams for {day} "
                            f"({len(excluded_teams)} disabled that day)")

    grounds = _grounds(sb)
    excluded_grounds = [g for g in grounds if S.is_disabled("ground", g, day, rules)]
    grounds = [g for g in grounds if g not in set(excluded_grounds)]
    hg = home_ground if body.ground_rotation == "home" else None

    # Don't repeat an opponent or a ground a team already has this weekend.
    avoid_pairs, team_grounds = _weekend_context(sb, poll_dates)
    result = build_round_robin(team_ids, _head_to_head(sb), grounds, hg,
                               avoid_pairs=avoid_pairs, team_grounds=team_grounds)
    ai = explain_schedule(result, team_names)

    fixtures = [{
        "home_team_id": p.home_team_id, "home_team": team_names.get(p.home_team_id, p.home_team_id),
        "away_team_id": p.away_team_id, "away_team": team_names.get(p.away_team_id, p.away_team_id),
        "ground_id": p.ground_id, "ground": S.ground_name(p.ground_id),
        "met_before": p.meetings_so_far, "reason": _reason(p, body.ground_rotation),
    } for p in result.pairings]

    gnames = {g["id"]: g["name"] for g in (S.GROUNDS)}
    payload = {
        "weekend_date": w.weekend_date.isoformat(),
        "date": target_date,
        "day": day,
        "fairness_score": result.fairness_score,
        "team_count": len(team_ids),
        "byes": [team_names.get(b, b) for b in result.byes],
        "fixtures": fixtures,
        "ai_explanation": ai["explanation"], "ai_source": ai["source"],
        "ground_rotation": body.ground_rotation,
        "excluded_teams": [team_names.get(t, t) for t in excluded_teams],
        "excluded_grounds": [gnames.get(g, g) for g in excluded_grounds],
    }
    _LAST.clear(); _LAST.update(payload)
    return payload


@router.get("/last")
def last(user: CurrentUser = Depends(require_admin)):
    return _LAST or {"fixtures": []}


@router.post("/apply")
def apply(body: ApplyScheduleRequest, user: CurrentUser = Depends(require_admin)):
    fixtures = body.fixtures or _LAST.get("fixtures")
    if not fixtures:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fixtures to apply — generate first")

    from datetime import date as _date
    cfg = window_config()
    w, meta = effective_windows(cfg, tz_now(cfg))
    sb = service_client()
    poll_dates = meta.get("dates") or [w.weekend_date.isoformat()]
    default_date = _LAST.get("date") or poll_dates[0]

    # Validate: no team gets the same opponent or ground twice this weekend
    # (across the submitted fixtures + anything already scheduled on these dates).
    existing_pairs, existing_grounds = _weekend_context(sb, poll_dates)
    errors = _validate_fixtures(fixtures, existing_pairs, existing_grounds)
    if errors:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "; ".join(dict.fromkeys(errors)))

    created = 0
    for f in fixtures:
        d = f.get("date") if f.get("date") in poll_dates else default_date
        when = datetime.combine(_date.fromisoformat(d), datetime.min.time(), tzinfo=timezone.utc).isoformat()
        row = {"home_team_id": f["home_team_id"], "away_team_id": f["away_team_id"],
               "ground_id": f.get("ground_id"), "scheduled_at": when, "status": "scheduled"}
        if sb is None:
            row["id"] = f"m{len(S.MATCHES) + 1:02d}"
            S.MATCHES.append(row)
        else:
            sb.table("matches").insert(row).execute()
        created += 1
    return {"ok": True, "created": created, "weekend_date": w.weekend_date.isoformat()}
