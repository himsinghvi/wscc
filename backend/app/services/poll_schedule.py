"""Admin-scheduled poll rounds (feature: schedule polling at a particular date/time).

An admin can create a one-off availability-poll round with explicit open /
publish / backout datetimes and a target weekend. When such a round is "current"
(live now, or the soonest upcoming one) it OVERRIDES the recurring weekly window.
When no scheduled round is live/upcoming, the system falls back to the recurring
weekly cadence from app_config.

Durable storage: Supabase `scheduled_polls` table when configured (works on
serverless/Vercel), else a local JSON file for offline dev. Server clock is
authoritative; all datetimes are stored tz-aware.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo

from ..core.time_windows import (
    WindowConfig, CycleWindows, current_cycle_windows,
    is_vote_open, is_published, is_backout_open, now as tz_now,
)
from ..core.supabase_client import service_client

_PATH = Path(__file__).resolve().parent.parent / "data" / "scheduled_polls.json"
_FIELDS = ("label", "weekend_date", "dates", "slots",
           "vote_open_at", "publish_at", "backout_close_at")

# dev-mode in-memory cache (mirrors the JSON file)
_POLLS: list[dict] = []


def _tz(cfg: WindowConfig) -> ZoneInfo:
    return ZoneInfo(cfg.timezone)


def _parse(dt: str, cfg: WindowConfig) -> datetime:
    """Parse an ISO datetime; if naive, interpret in the app timezone."""
    d = datetime.fromisoformat(str(dt))
    if d.tzinfo is None:
        d = d.replace(tzinfo=_tz(cfg))
    return d


def _load():
    global _POLLS
    if _PATH.exists():
        try:
            _POLLS = json.loads(_PATH.read_text(encoding="utf-8"))
        except Exception:
            _POLLS = []


def _save():
    try:
        _PATH.write_text(json.dumps(_POLLS, indent=2), encoding="utf-8")
    except Exception:
        pass


_load()


def _all_polls() -> list[dict]:
    """All scheduled polls — from Supabase when configured, else the JSON cache."""
    sb = service_client()
    if sb is None:
        return list(_POLLS)
    try:
        return sb.table("scheduled_polls").select("*").execute().data or []
    except Exception:
        return []


def list_polls() -> list[dict]:
    return sorted(_all_polls(), key=lambda p: str(p["vote_open_at"]))


DEFAULT_SLOTS = ["1st", "2nd"]


def _build_poll(cfg: WindowConfig, *, label, vote_open_at, publish_at,
                backout_close_at, weekend_date, dates, slots=None) -> dict:
    """Validate + normalise poll fields (shared by create/update)."""
    from datetime import datetime as _dt, time as _time
    tz = _tz(cfg)
    open_dt = _parse(vote_open_at, cfg)
    pub_dt = _parse(publish_at, cfg) if publish_at else open_dt + timedelta(hours=6)

    # dates admins are collecting availability for
    date_list = sorted({date.fromisoformat(d).isoformat() for d in (dates or []) if d})
    if not date_list:
        if weekend_date:
            date_list = [date.fromisoformat(weekend_date).isoformat()]
        else:
            nxt = open_dt.date() + timedelta(days=(5 - open_dt.date().weekday()) % 7)
            date_list = [nxt.isoformat()]
    wk = date.fromisoformat(weekend_date).isoformat() if weekend_date else date_list[0]

    # Backout opens when results publish and stays open until the admin-set
    # "backout open until" date (end of that day). Defaults to the last match
    # date if the admin leaves it blank. A date-only value means end-of-day.
    if backout_close_at:
        s = backout_close_at
        if len(s) == 10:            # "YYYY-MM-DD" → end of that day
            s += "T23:59:59"
        bak_dt = _parse(s, cfg)
    else:
        bak_dt = _dt.combine(date.fromisoformat(date_list[-1]), _time(23, 59, 59), tz)
    if not (open_dt < pub_dt <= bak_dt):
        raise ValueError("vote_open < publish is required, and the backout-until "
                         "date must be on/after publish")

    # time-slots per day (e.g. 1st / 2nd match). '#' is reserved as the token separator.
    slot_list = [s.strip().replace("#", "") for s in (slots or []) if s and s.strip()]
    if not slot_list:
        slot_list = list(DEFAULT_SLOTS)

    return {
        "label": (label or f"Poll for {wk}").strip(),
        "weekend_date": wk,
        "dates": date_list,
        "slots": slot_list,
        "vote_open_at": open_dt.astimezone(tz).isoformat(),
        "publish_at": pub_dt.astimezone(tz).isoformat(),
        "backout_close_at": bak_dt.astimezone(tz).isoformat(),
    }


def create_poll(cfg: WindowConfig, *, label=None, vote_open_at, publish_at=None,
                backout_close_at=None, weekend_date=None, dates=None, slots=None, created_by=None) -> dict:
    fields = _build_poll(cfg, label=label, vote_open_at=vote_open_at, publish_at=publish_at,
                         backout_close_at=backout_close_at, weekend_date=weekend_date,
                         dates=dates, slots=slots)
    sb = service_client()
    if sb is None:
        poll = {"id": str(uuid.uuid4()), **fields,
                "created_by": created_by, "created_at": datetime.now(_tz(cfg)).isoformat()}
        _POLLS.append(poll); _save()
        return poll
    row = {**fields, "created_by": created_by}
    return sb.table("scheduled_polls").insert(row).execute().data[0]


def update_poll(cfg: WindowConfig, poll_id: str, **kwargs) -> dict | None:
    sb = service_client()
    poll = (next((p for p in _POLLS if p["id"] == poll_id), None) if sb is None
            else (sb.table("scheduled_polls").select("*").eq("id", poll_id).execute().data or [None])[0])
    if not poll:
        return None
    fields = _build_poll(
        cfg,
        label=kwargs.get("label") if kwargs.get("label") is not None else poll.get("label"),
        vote_open_at=kwargs.get("vote_open_at") or poll["vote_open_at"],
        publish_at=kwargs.get("publish_at") or poll["publish_at"],
        backout_close_at=kwargs.get("backout_close_at"),  # re-derive from dates
        weekend_date=kwargs.get("weekend_date") or poll.get("weekend_date"),
        dates=kwargs.get("dates") if kwargs.get("dates") is not None else poll.get("dates"),
        slots=kwargs.get("slots") if kwargs.get("slots") is not None else poll.get("slots"),
    )
    if sb is None:
        poll.update(fields); _save()
        return poll
    return sb.table("scheduled_polls").update(fields).eq("id", poll_id).execute().data[0]


def delete_poll(poll_id: str) -> bool:
    global _POLLS
    sb = service_client()
    if sb is None:
        n = len(_POLLS)
        _POLLS = [p for p in _POLLS if p["id"] != poll_id]
        if len(_POLLS) != n:
            _save(); return True
        return False
    res = sb.table("scheduled_polls").delete().eq("id", poll_id).execute()
    return bool(res.data)


def _to_windows(poll: dict, cfg: WindowConfig) -> CycleWindows:
    return CycleWindows(
        weekend_date=date.fromisoformat(str(poll["weekend_date"])[:10]),
        vote_open_at=_parse(poll["vote_open_at"], cfg),
        publish_at=_parse(poll["publish_at"], cfg),
        backout_close_at=_parse(poll["backout_close_at"], cfg),
    )


def current_scheduled(cfg: WindowConfig, ref: datetime) -> dict | None:
    """Pick the governing scheduled poll for `ref`: the live one (open..backout),
    else the soonest upcoming one. Fully-past rounds are ignored."""
    live, upcoming = [], []
    for p in _all_polls():
        o = _parse(p["vote_open_at"], cfg)
        b = _parse(p["backout_close_at"], cfg)
        if o <= ref < b:
            live.append((o, p))
        elif ref < o:
            upcoming.append((o, p))
    if live:
        return sorted(live, key=lambda x: x[0])[-1][1]   # most-recently-opened live
    if upcoming:
        return sorted(upcoming, key=lambda x: x[0])[0][1]  # soonest upcoming
    return None


def effective_windows(cfg: WindowConfig, ref: datetime) -> tuple[CycleWindows, dict]:
    """Return the windows in force now + metadata about their source."""
    poll = current_scheduled(cfg, ref)
    if poll:
        return _to_windows(poll, cfg), {"source": "scheduled", "poll_id": poll["id"],
                                        "label": poll["label"],
                                        "dates": poll.get("dates") or [poll["weekend_date"]],
                                        "slots": poll.get("slots") or DEFAULT_SLOTS}
    w = current_cycle_windows(cfg, ref)
    return w, {"source": "recurring", "poll_id": None, "label": "Weekly schedule",
               "dates": [w.weekend_date.isoformat()], "slots": DEFAULT_SLOTS}


def summary(cfg: WindowConfig, ref: datetime | None = None) -> dict:
    """Phase + windows for the effective (scheduled or recurring) round."""
    r = ref or tz_now(cfg)
    w, meta = effective_windows(cfg, r)
    if r < w.vote_open_at:
        phase = "before_open"
    elif is_vote_open(w, cfg, r):
        phase = "voting_open"
    elif is_backout_open(w, cfg, r):
        phase = "backout_open"
    else:
        phase = "closed"
    return {
        "server_time": r.isoformat(), "timezone": cfg.timezone,
        "weekend_date": w.weekend_date.isoformat(),
        "vote_open_at": w.vote_open_at.isoformat(),
        "publish_at": w.publish_at.isoformat(),
        "backout_close_at": w.backout_close_at.isoformat(),
        "phase": phase,
        "vote_open": is_vote_open(w, cfg, r),
        "published": is_published(w, cfg, r),
        "backout_open": is_backout_open(w, cfg, r),
        "source": meta["source"], "poll_id": meta["poll_id"], "poll_label": meta["label"],
        "dates": meta.get("dates", [w.weekend_date.isoformat()]),
        "slots": meta.get("slots", DEFAULT_SLOTS),
    }
