"""Loads admin-tunable settings from app_config into a WindowConfig.

Falls back to defaults when Supabase is not configured (dev mode).
"""
from datetime import time

from ..core.config import settings
from ..core.supabase_client import service_client
from ..core.time_windows import WindowConfig

_DEFAULTS = dict(
    timezone=settings.app_timezone,
    vote_weekday=1,
    vote_open_time="11:00:00",
    publish_time="18:00:00",
    backout_weekday=4,
    backout_close_time="18:00:00",
    max_voting_teams=0,          # 0 = all teams in the league (no cap)
    max_sessions_per_team=2,
    session_policy="block_new",
    reject_early_votes=False,
)


def league_team_count() -> int:
    sb = service_client()
    if sb is not None:
        try:
            r = sb.table("teams").select("id", count="exact").execute()
            if r.count is not None:
                return r.count
        except Exception:
            pass
    from ..core import sampledata as S
    return len(S.TEAMS)


def effective_max_voting_teams(cfg: dict) -> int:
    """Resolve the voting cap: a configured positive value, else the whole league."""
    v = cfg.get("max_voting_teams")
    try:
        v = int(v)
    except (TypeError, ValueError):
        v = 0
    return v if v and v > 0 else league_team_count()


def _parse_time(v) -> time:
    if isinstance(v, time):
        return v
    h, m, s = (list(map(int, str(v).split(":"))) + [0, 0, 0])[:3]
    return time(h, m, s)


def load_config() -> dict:
    sb = service_client()
    if sb is None:
        return dict(_DEFAULTS)
    res = sb.table("app_config").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else dict(_DEFAULTS)


def window_config() -> WindowConfig:
    c = load_config()
    return WindowConfig(
        timezone=c.get("timezone", settings.app_timezone),
        vote_weekday=c.get("vote_weekday", 1),
        vote_open_time=_parse_time(c.get("vote_open_time", "11:00:00")),
        publish_time=_parse_time(c.get("publish_time", "18:00:00")),
        backout_weekday=c.get("backout_weekday", 4),
        backout_close_time=_parse_time(c.get("backout_close_time", "18:00:00")),
    )
