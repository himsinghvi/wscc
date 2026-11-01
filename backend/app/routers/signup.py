"""Team-select signup with admin approval + max 2 members per team.

Flow: a signed-in-but-unapproved user POSTs a request choosing their team.
An admin approves → the email is added to allowed_emails (+players) so they can
use the app. Until then the frontend shows a "waiting for approval" screen.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from ..core.auth import CurrentUser, require_admin, bearer_email
from ..core.supabase_client import service_client

router = APIRouter(prefix="/signup", tags=["signup"])
MAX_PER_TEAM = 2


class SignupRequest(BaseModel):
    team_id: str
    full_name: Optional[str] = None


def _approved_members(sb, team_id: str) -> int:
    """Count approved, non-admin members already on a team."""
    rows = (sb.table("allowed_emails").select("email,role")
            .eq("team_id", team_id).eq("is_active", True).execute().data)
    return sum(1 for r in rows if r.get("role") != "admin")


@router.post("/request")
def request_signup(body: SignupRequest, authorization: Optional[str] = Header(None)):
    email = bearer_email(authorization)        # 401 if not signed in
    sb = service_client()
    if sb is None:
        return {"status": "ok", "dev_mode": True}

    team = sb.table("teams").select("id,name").eq("id", body.team_id).execute().data
    if not team:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pick a valid team")
    # already approved? nothing to do
    if sb.table("allowed_emails").select("email").eq("email", email).eq("is_active", True).execute().data:
        return {"status": "ok"}
    if _approved_members(sb, body.team_id) >= MAX_PER_TEAM:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"{team[0]['name']} already has {MAX_PER_TEAM} approved members.")

    sb.table("signup_requests").upsert({
        "email": email, "team_id": body.team_id, "full_name": body.full_name,
        "status": "pending", "decided_by": None, "decided_at": None,
    }).execute()
    return {"status": "pending", "team": team[0]["name"]}


@router.get("/requests")
def list_requests(user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    if sb is None:
        return {"requests": []}
    reqs = sb.table("signup_requests").select("*").order("created_at").execute().data
    teams = {t["id"]: t for t in sb.table("teams").select("id,name,short_name").execute().data}
    out = []
    for r in reqs:
        tid = r.get("team_id")
        out.append({**r, "team": teams.get(tid, {}).get("name"),
                    "team_members": _approved_members(sb, tid) if tid else 0,
                    "team_full": (tid and _approved_members(sb, tid) >= MAX_PER_TEAM)})
    return {"requests": out, "max_per_team": MAX_PER_TEAM}


@router.post("/requests/{email}/approve")
def approve(email: str, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    r = sb.table("signup_requests").select("*").eq("email", email).execute().data
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such request")
    team_id = r[0].get("team_id")
    if team_id and _approved_members(sb, team_id) >= MAX_PER_TEAM:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Team already has {MAX_PER_TEAM} approved members.")

    sb.table("allowed_emails").upsert({
        "email": email, "team_id": team_id, "role": "team_rep", "is_active": True},
        on_conflict="email").execute()
    sb.table("players").upsert({
        "email": email, "full_name": r[0].get("full_name"), "team_id": team_id,
        "role": "team_rep", "is_rep": True}, on_conflict="email").execute()
    sb.table("signup_requests").update({
        "status": "approved", "decided_by": user.player_id,
        "decided_at": datetime.now(timezone.utc).isoformat()}).eq("email", email).execute()
    return {"ok": True, "email": email, "status": "approved"}


@router.post("/requests/{email}/reject")
def reject(email: str, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    sb.table("signup_requests").update({
        "status": "rejected", "decided_by": user.player_id,
        "decided_at": datetime.now(timezone.utc).isoformat()}).eq("email", email).execute()
    sb.table("allowed_emails").update({"is_active": False}).eq("email", email).execute()
    return {"ok": True, "email": email, "status": "rejected"}
