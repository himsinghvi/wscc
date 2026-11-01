"""Active-session registry — enforces max 2 logins per team (feature 2).

The frontend registers its session after sign-in; the backend decides whether
a new session is allowed based on app_config.max_sessions_per_team and
session_policy. This is server-owned and cannot be bypassed by the client.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import CurrentUser, get_current_user
from ..core.supabase_client import service_client
from ..schemas import SessionRegister
from ..services.config_service import load_config

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/register")
def register_session(body: SessionRegister, user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    cfg = load_config()
    max_sessions = cfg.get("max_sessions_per_team", 2)
    policy = cfg.get("session_policy", "block_new")

    if sb is None:
        return {"allowed": True, "dev_mode": True, "max_sessions_per_team": max_sessions}
    if not user.team_id:
        # admins / league officials aren't tied to a team — no per-team cap applies
        return {"allowed": True, "no_team": True}

    active = (sb.table("active_sessions").select("*")
              .eq("team_id", user.team_id).is_("revoked_at", "null")
              .order("created_at").execute()).data

    # already registered? refresh last_seen
    for s in active:
        if s["jti"] == body.jti:
            sb.table("active_sessions").update({"last_seen": "now()"}).eq("id", s["id"]).execute()
            return {"allowed": True, "active_count": len(active)}

    if len(active) >= max_sessions:
        if policy == "evict_oldest":
            oldest = active[0]
            sb.table("active_sessions").update({"revoked_at": "now()"}).eq("id", oldest["id"]).execute()
        else:  # block_new
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Team already has {max_sessions} active logins. Ask a teammate to log out.",
            )

    sb.table("active_sessions").insert({
        "player_id": user.player_id, "team_id": user.team_id,
        "jti": body.jti, "user_agent": body.user_agent,
    }).execute()
    return {"allowed": True, "active_count": min(len(active) + 1, max_sessions)}


@router.post("/logout")
def logout(body: SessionRegister, user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    if sb is None:
        return {"ok": True, "dev_mode": True}
    sb.table("active_sessions").update({"revoked_at": "now()"}) \
        .eq("jti", body.jti).eq("player_id", user.player_id).execute()
    return {"ok": True}


@router.get("/mine")
def my_team_sessions(user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    if sb is None or not user.team_id:
        return {"active": [], "dev_mode": sb is None}
    active = (sb.table("active_sessions").select("id,user_agent,created_at,last_seen")
              .eq("team_id", user.team_id).is_("revoked_at", "null").execute()).data
    return {"active": active, "max": load_config().get("max_sessions_per_team", 2)}
