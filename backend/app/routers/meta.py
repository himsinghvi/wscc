"""Time-window state + current user — the clock the whole UI trusts."""
from fastapi import APIRouter, Depends

from ..core.auth import CurrentUser, get_current_user
from ..core.supabase_client import is_configured
from ..core import sampledata as S
from ..services import poll_schedule
from ..services.config_service import window_config, load_config

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/time")
def time_state():
    """Server clock + the current cycle's phase/windows (scheduled override or
    weekly default). The frontend renders countdowns from this and never decides
    open/closed itself."""
    return poll_schedule.summary(window_config())


def _capabilities(user: CurrentUser) -> list[str]:
    """What this persona may do. Everyone reads; admins manage; team personas
    (reps/players) participate in polls."""
    caps = {"read", "schedule.view"}
    if user.is_admin:
        caps |= {"schedule.manage", "poll.manage", "rules.manage", "admin.config",
                 "teams.manage", "grounds.manage"}
    else:
        caps |= {"availability.submit"}
    return sorted(caps)


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return {
        "email": user.email,
        "player_id": user.player_id,
        "team_id": user.team_id,
        "role": user.role,
        "is_rep": user.is_rep,
        "is_admin": user.is_admin,
        "capabilities": _capabilities(user),
    }


@router.get("/test-accounts")
def test_accounts():
    """Dev-only quick-login accounts (one admin + one rep per team). Empty when a
    real Supabase backend is configured, so it never leaks in production."""
    if is_configured():
        return {"dev_mode": False, "accounts": []}
    return {"dev_mode": True, "accounts": S.dev_accounts(12)}


@router.get("/config/public")
def public_config():
    c = load_config()
    return {
        "timezone": c.get("timezone"),
        "max_voting_teams": c.get("max_voting_teams"),
        "vote_open_time": str(c.get("vote_open_time")),
        "publish_time": str(c.get("publish_time")),
        "backout_close_time": str(c.get("backout_close_time")),
    }
