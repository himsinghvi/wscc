"""Availability voting, ranking & backout (features 3, 3b, 4, 6).

Everything that matters is decided server-side:
  * `submitted_at` is stamped with the SERVER clock at millisecond precision.
  * Submissions are only accepted while the vote window is open; a vote that
    lands before Monday 11:00 is flagged `is_early` (shown 🔴, excluded from
    the valid first-come ranking) unless `reject_early_votes` is on.
  * The published ranking (first-come) is only returned after publish time.
  * No more than `max_voting_teams` distinct teams may register a submission.
  * Backout is only allowed during the backout window (before Thu 18:00).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core.supabase_client import service_client
from ..core.time_windows import (
    current_cycle_windows, is_vote_open, is_backout_open, is_published, is_early, now as tz_now,
)
from ..schemas import AvailabilitySubmit, BackoutRequest
from ..services.config_service import window_config, load_config, effective_max_voting_teams
from ..services.poll_schedule import effective_windows

router = APIRouter(prefix="/availability", tags=["availability"])


# ------------------------------------------------------------------
# In-memory store for dev mode (no Supabase). Keyed by weekend_date.
# ------------------------------------------------------------------
_DEV_STORE: dict[str, list[dict]] = {}

def _ms(dt: datetime) -> int:
    return int(dt.astimezone(timezone.utc).timestamp() * 1000)


# availability tokens: "YYYY-MM-DD#slot" (one per date+slot the team can play)
def _all_tokens(dates: list[str], slots: list[str]) -> list[str]:
    return [f"{d}#{s}" for d in dates for s in slots]


def _dates_from(tokens: list[str]) -> list[str]:
    return sorted({t.split("#", 1)[0] for t in tokens})


def _current_slots(mine: dict, poll_dates: list[str], poll_slots: list[str]) -> list[str]:
    """A submission's current (date#slot) tokens, back-filled for older rows."""
    cur = mine.get("available_slots")
    if cur is not None:
        return list(cur)
    cd = mine.get("available_dates") or poll_dates
    return _all_tokens(cd, poll_slots)


def _team_name(sb, team_id: str) -> str:
    if sb is None:
        from ..core import sampledata as S
        return S.team_name(team_id)
    r = sb.table("teams").select("name").eq("id", team_id).execute()
    return r.data[0]["name"] if r.data else team_id


@router.get("/status")
def status_(user: CurrentUser = Depends(get_current_user)):
    cfg = window_config()
    r = tz_now(cfg)
    w, wmeta = effective_windows(cfg, r)
    sb = service_client()

    rows = _current_rows(sb, w.weekend_date.isoformat())
    voted = any(x["team_id"] == user.team_id for x in rows) if user.team_id else False
    mine = next((x for x in rows if x["team_id"] == user.team_id), None)

    return {
        "weekend_date": w.weekend_date.isoformat(),
        "vote_open": is_vote_open(w, cfg, r),
        "published": is_published(w, cfg, r),
        # Backout is allowed from the moment a team has opted in, right up to the
        # backout close time (it no longer waits for results to publish).
        "backout_open": voted and r < w.backout_close_at,
        "vote_open_at": w.vote_open_at.isoformat(),
        "publish_at": w.publish_at.isoformat(),
        "backout_close_at": w.backout_close_at.isoformat(),
        "teams_voted": len(rows),
        "max_voting_teams": effective_max_voting_teams(load_config()),
        "has_voted": voted,
        "my_submission": mine,
        "source": wmeta["source"],
        "poll_label": wmeta["label"],
        "dates": wmeta.get("dates", [w.weekend_date.isoformat()]),
        "slots": wmeta.get("slots", ["1st", "2nd"]),
        "my_available_dates": (mine or {}).get("available_dates"),
        "my_available_slots": (mine or {}).get("available_slots"),
        "my_backed_out_slots": (mine or {}).get("backed_out_slots"),
    }


def _current_rows(sb, weekend_date: str) -> list[dict]:
    if sb is None:
        return _DEV_STORE.get(weekend_date, [])
    cyc = sb.table("vote_cycles").select("id").eq("weekend_date", weekend_date).execute()
    if not cyc.data:
        return []
    cid = cyc.data[0]["id"]
    return (sb.table("availability").select("*").eq("cycle_id", cid)
            .order("submitted_at").execute()).data


def _ensure_cycle(sb, w, cfg) -> str:
    """Return cycle_id, creating the vote_cycles row if needed (Supabase mode)."""
    wd = w.weekend_date.isoformat()
    existing = sb.table("vote_cycles").select("id").eq("weekend_date", wd).execute()
    if existing.data:
        return existing.data[0]["id"]
    created = sb.table("vote_cycles").insert({
        "weekend_date": wd,
        "vote_open_at": w.vote_open_at.isoformat(),
        "publish_at": w.publish_at.isoformat(),
        "backout_close_at": w.backout_close_at.isoformat(),
        "max_voting_teams": load_config().get("max_voting_teams", 8),
    }).execute()
    return created.data[0]["id"]


@router.post("/submit")
def submit(body: AvailabilitySubmit, user: CurrentUser = Depends(get_current_user)):
    cfg = window_config()
    full_cfg = load_config()
    server_now = tz_now(cfg)              # authoritative server clock, ms precision
    w, wmeta = effective_windows(cfg, server_now)
    sb = service_client()

    if user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Admins manage polls and don't submit team availability.")
    if not user.team_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You are not linked to a team")

    early = is_early(server_now, w)
    if early and full_cfg.get("reject_early_votes", False):
        raise HTTPException(status.HTTP_425_TOO_EARLY,
                            "Voting has not opened yet (Monday 11:00).")
    if not early and not is_vote_open(w, cfg, server_now):
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Voting window is closed for this weekend.")

    rows = _current_rows(sb, w.weekend_date.isoformat())
    already = next((x for x in rows if x["team_id"] == user.team_id), None)
    if already:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Your team has already submitted availability.")

    # Feature 6: cap on number of teams that may vote (0/unset = whole league).
    max_teams = effective_max_voting_teams(full_cfg)
    distinct_teams = {x["team_id"] for x in rows}
    if user.team_id not in distinct_teams and len(distinct_teams) >= max_teams:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Voting is full ({max_teams} teams already submitted).")

    # Which (date, slot) combinations the team can play (subset of the poll's).
    poll_dates = wmeta.get("dates") or [w.weekend_date.isoformat()]
    poll_slots = wmeta.get("slots") or ["1st", "2nd"]
    all_tokens = _all_tokens(poll_dates, poll_slots)
    if body.available_slots is not None:
        chosen = [t for t in body.available_slots if t in all_tokens]
    elif body.available_dates is not None:
        picked = set(body.available_dates)
        chosen = [t for t in all_tokens if t.split("#", 1)[0] in picked]
    else:
        chosen = list(all_tokens)               # default: available for everything
    if not chosen:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Select at least one slot your team is available for.")
    avail_dates = _dates_from(chosen)

    record = {
        "team_id": user.team_id, "submitted_by": user.player_id,
        "submitted_at": server_now.isoformat(), "submitted_at_ms": _ms(server_now),
        "status": "available", "is_early": early, "note": body.note,
        "available_slots": chosen, "available_dates": avail_dates,
    }

    if sb is None:
        _DEV_STORE.setdefault(w.weekend_date.isoformat(), []).append(record)
    else:
        cid = _ensure_cycle(sb, w, cfg)
        sb.table("availability").insert({
            "cycle_id": cid, "team_id": user.team_id, "submitted_by": user.player_id,
            "status": "available", "is_early": early, "note": body.note,
            "available_slots": chosen, "available_dates": avail_dates,
        }).execute()

    return {"ok": True, "submitted_at": server_now.isoformat(),
            "submitted_at_ms": _ms(server_now), "is_early": early,
            "available_slots": chosen, "available_dates": avail_dates,
            "message": "Availability recorded." + (" (early — will show in red)" if early else "")}


@router.post("/backout")
def backout(body: BackoutRequest, user: CurrentUser = Depends(get_current_user)):
    cfg = window_config()
    server_now = tz_now(cfg)
    w, wmeta = effective_windows(cfg, server_now)
    sb = service_client()

    if user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Admins manage polls and don't submit team availability.")
    if server_now >= w.backout_close_at:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Backout window has closed.")

    rows = _current_rows(sb, w.weekend_date.isoformat())
    mine = next((x for x in rows if x["team_id"] == user.team_id), None)
    if not mine:
        # backout only makes sense once a team has opted in
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Your team hasn't opted in yet.")

    poll_dates = wmeta.get("dates") or [w.weekend_date.isoformat()]
    poll_slots = wmeta.get("slots") or ["1st", "2nd"]
    current = _current_slots(mine, poll_dates, poll_slots)

    # which (date#slot) tokens to back out of
    if body.slots is not None:
        to_remove = [t for t in body.slots if t in current]
    elif body.dates is not None:
        drop = set(body.dates)
        to_remove = [t for t in current if t.split("#", 1)[0] in drop]
    else:
        to_remove = list(current)               # back out of everything
    if not to_remove:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No matching slots to back out of.")

    remaining = [t for t in current if t not in to_remove]
    backed = sorted(set((mine.get("backed_out_slots") or []) + to_remove))
    new_status = "backed_out" if not remaining else "available"
    rem_dates = _dates_from(remaining)

    if sb is None:
        mine.update({"available_slots": remaining, "backed_out_slots": backed,
                     "available_dates": rem_dates, "status": new_status,
                     "backed_out_at": server_now.isoformat(),
                     "note": body.reason or mine.get("note")})
    else:
        cid = _ensure_cycle(sb, w, cfg)
        sb.table("availability").update({
            "available_slots": remaining, "backed_out_slots": backed,
            "available_dates": rem_dates, "status": new_status,
            "backed_out_at": server_now.isoformat(), "backed_out_by": user.player_id,
            "note": body.reason,
        }).eq("cycle_id", cid).eq("team_id", user.team_id).execute()

    return {"ok": True, "status": new_status, "at": server_now.isoformat(),
            "available_slots": remaining, "backed_out_slots": backed, "available_dates": rem_dates}


@router.get("/rankings")
def rankings(user: CurrentUser = Depends(get_current_user)):
    """Published first-come ranking (feature 3b).

    Ordered ascending by submitted_at (millisecond precision). Early votes
    (before 11:00) are flagged red and placed first but NOT given a valid rank;
    valid votes are green and ranked 1..N by arrival time.
    """
    cfg = window_config()
    server_now = tz_now(cfg)
    w, wmeta = effective_windows(cfg, server_now)
    sb = service_client()
    published = is_published(w, cfg, server_now)

    # Before publish, only an admin may preview the ordering.
    if not published and not user.is_admin:
        return {"published": False, "publish_at": w.publish_at.isoformat(), "rows": []}

    rows = _current_rows(sb, w.weekend_date.isoformat())

    def parse_ts(x) -> datetime:
        v = x.get("submitted_at")
        return datetime.fromisoformat(v) if isinstance(v, str) else v

    ordered = sorted(rows, key=parse_ts)
    out, rank = [], 0
    for x in ordered:
        ts = parse_ts(x)
        early = x.get("is_early", False)
        if not early:
            rank += 1
        out.append({
            "rank": None if early else rank,
            "team_id": x["team_id"],
            "team_name": _team_name(sb, x["team_id"]),
            "submitted_at": ts.isoformat(),
            "submitted_at_ms": x.get("submitted_at_ms") or _ms(ts),
            "is_early": early,
            "status": x.get("status", "available"),
            "color": "red" if early else "green",
            "available_dates": x.get("available_dates"),
            "available_slots": x.get("available_slots"),
        })

    return {"published": published, "publish_at": w.publish_at.isoformat(),
            "weekend_date": w.weekend_date.isoformat(),
            "dates": wmeta.get("dates", [w.weekend_date.isoformat()]),
            "slots": wmeta.get("slots", ["1st", "2nd"]), "rows": out}
