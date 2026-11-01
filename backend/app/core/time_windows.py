"""Server-authoritative time-window logic (features 3, 3b, 4).

All decisions about *when* voting opens, when results publish, and when backout
closes are computed here from `app_config`, using the server clock in the
configured timezone. The client is never trusted for timing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
from zoneinfo import ZoneInfo


@dataclass
class WindowConfig:
    timezone: str = "Asia/Kolkata"
    vote_weekday: int = 1          # ISO: Mon=1 .. Sun=7
    vote_open_time: time = time(11, 0, 0)
    publish_time: time = time(18, 0, 0)
    backout_weekday: int = 4       # Thu
    backout_close_time: time = time(18, 0, 0)


@dataclass
class CycleWindows:
    weekend_date: date             # Saturday of the target weekend
    vote_open_at: datetime         # Monday 11:00 (tz-aware)
    publish_at: datetime           # Monday 18:00
    backout_close_at: datetime     # Thursday 18:00


def _tz(cfg: WindowConfig) -> ZoneInfo:
    return ZoneInfo(cfg.timezone)


def now(cfg: WindowConfig) -> datetime:
    return datetime.now(_tz(cfg))


def _next_or_same_weekday(ref: date, iso_weekday: int) -> date:
    """First date >= ref whose ISO weekday == iso_weekday."""
    delta = (iso_weekday - ref.isoweekday()) % 7
    return ref + timedelta(days=delta)


def current_cycle_windows(cfg: WindowConfig, ref: datetime | None = None) -> CycleWindows:
    """Compute the windows for the *current* voting cycle.

    The cycle is anchored on the **upcoming weekend** — the next Saturday on or
    after `ref`'s date. Its Monday 11:00 opening therefore lies in that weekend's
    own week, so a vote cast Monday morning (before 11:00) correctly belongs to
    the upcoming weekend and is flagged *early* (🔴) rather than rolling into the
    previous cycle. The weekend rolls over on Sunday once Saturday has passed.
    """
    tz = _tz(cfg)
    ref = (ref or datetime.now(tz)).astimezone(tz)

    # Upcoming Saturday (ISO weekday 6) on or after today.
    days_to_sat = (6 - ref.date().isoweekday()) % 7
    saturday = ref.date() + timedelta(days=days_to_sat)
    # Monday of that weekend's week (vote opens here).
    this_monday = saturday - timedelta(days=5)

    vote_open = datetime.combine(this_monday, cfg.vote_open_time, tz)
    publish_at = datetime.combine(this_monday, cfg.publish_time, tz)
    thursday = this_monday + timedelta(days=(cfg.backout_weekday - 1))
    backout_close = datetime.combine(thursday, cfg.backout_close_time, tz)

    return CycleWindows(
        weekend_date=saturday,
        vote_open_at=vote_open,
        publish_at=publish_at,
        backout_close_at=backout_close,
    )


# ---- state helpers -------------------------------------------------

def is_vote_open(w: CycleWindows, cfg: WindowConfig, ref: datetime | None = None) -> bool:
    ref = ref or now(cfg)
    # Voting is open from Monday 11:00 up to publish (Monday 18:00).
    return w.vote_open_at <= ref < w.publish_at


def is_published(w: CycleWindows, cfg: WindowConfig, ref: datetime | None = None) -> bool:
    return (ref or now(cfg)) >= w.publish_at


def is_backout_open(w: CycleWindows, cfg: WindowConfig, ref: datetime | None = None) -> bool:
    ref = ref or now(cfg)
    return w.publish_at <= ref < w.backout_close_at


def is_early(submitted_at: datetime, w: CycleWindows) -> bool:
    """True if a vote landed before the official open → shown 🔴, excluded from rank."""
    return submitted_at < w.vote_open_at


def state_summary(cfg: WindowConfig, ref: datetime | None = None) -> dict:
    w = current_cycle_windows(cfg, ref)
    r = ref or now(cfg)
    if r < w.vote_open_at:
        phase = "before_open"
    elif is_vote_open(w, cfg, r):
        phase = "voting_open"
    elif is_backout_open(w, cfg, r):
        phase = "backout_open"
    else:
        phase = "closed"
    return {
        "server_time": r.isoformat(),
        "timezone": cfg.timezone,
        "weekend_date": w.weekend_date.isoformat(),
        "vote_open_at": w.vote_open_at.isoformat(),
        "publish_at": w.publish_at.isoformat(),
        "backout_close_at": w.backout_close_at.isoformat(),
        "phase": phase,
        "vote_open": is_vote_open(w, cfg, r),
        "published": is_published(w, cfg, r),
        "backout_open": is_backout_open(w, cfg, r),
    }
