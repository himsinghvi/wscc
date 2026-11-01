"""Time-window state + current user — the clock the whole UI trusts."""
from fastapi import APIRouter, Depends

from typing import Optional
from fastapi import Header

from ..core.auth import (CurrentUser, get_current_user, bearer_claims, _lookup_player)
from ..core.supabase_client import is_configured, service_client
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
                 "teams.manage", "grounds.manage", "signup.approve"}
    else:
        caps |= {"availability.submit"}
    return sorted(caps)


def _profile(user: CurrentUser) -> dict:
    return {
        "status": "ok",
        "email": user.email, "player_id": user.player_id, "team_id": user.team_id,
        "role": user.role, "is_rep": user.is_rep, "is_admin": user.is_admin,
        "capabilities": _capabilities(user),
    }


@router.get("/me")
def me(authorization: Optional[str] = Header(None), x_dev_email: Optional[str] = Header(None)):
    """Returns the caller's status: 'ok' (approved), 'pending'/'rejected'
    (awaiting admin), or 'unregistered' (signed in but no request yet)."""
    if not is_configured():
        return _profile(_lookup_player(x_dev_email or "admin@wscc.app", None))

    claims = bearer_claims(authorization)  # 401 if no/invalid token
    email = claims.get("email"); sub = claims.get("sub")
    sb = service_client()
    approved = sb.table("allowed_emails").select("email").eq("email", email).eq("is_active", True).execute().data
    if approved:
        return _profile(_lookup_player(email, sub))
    req = sb.table("signup_requests").select("*").eq("email", email).execute().data
    if req:
        r = req[0]
        tname = (sb.table("teams").select("name").eq("id", r["team_id"]).execute().data or [{}])[0].get("name") if r.get("team_id") else None
        return {"status": r["status"], "email": email, "team_id": r.get("team_id"), "team": tname}
    return {"status": "unregistered", "email": email}


@router.get("/teams-public")
def teams_public():
    """Minimal team list for the signup dropdown (no auth required)."""
    sb = service_client()
    if sb is None:
        return {"teams": [{"id": t["id"], "name": t["name"], "short_name": t["short_name"]} for t in S.TEAMS]}
    rows = sb.table("teams").select("id,name,short_name").order("name").execute().data
    return {"teams": rows}


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
