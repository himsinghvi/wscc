"""Admin configuration (features 4 & 6) — admin-only, audited."""
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import CurrentUser, require_admin
from ..core.supabase_client import service_client
from ..schemas import ConfigUpdate
from ..services.config_service import load_config

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/config")
def get_config(user: CurrentUser = Depends(require_admin)):
    return load_config()


@router.put("/config")
def update_config(body: ConfigUpdate, user: CurrentUser = Depends(require_admin)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")

    sb = service_client()
    if sb is None:
        return {"ok": True, "dev_mode": True, "applied": patch,
                "note": "Supabase not configured; change not persisted."}

    patch["updated_by"] = user.player_id
    sb.table("app_config").update(patch).eq("id", 1).execute()
    sb.table("audit_log").insert({
        "actor_id": user.player_id, "action": "config.update",
        "entity": "app_config", "entity_id": "1", "detail": patch,
    }).execute()
    return {"ok": True, "applied": patch}


@router.get("/allowlist")
def get_allowlist(user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    if sb is None:
        return {"dev_mode": True, "emails": []}
    return {"emails": sb.table("allowed_emails").select("*").execute().data}


@router.post("/allowlist")
def add_allowlist(email: str, team_id: str | None = None, role: str = "player",
                  user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    if sb is None:
        return {"ok": True, "dev_mode": True}
    sb.table("allowed_emails").upsert(
        {"email": email, "team_id": team_id, "role": role, "is_active": True}
    ).execute()
    sb.table("audit_log").insert({
        "actor_id": user.player_id, "action": "allowlist.add",
        "entity": "allowed_emails", "entity_id": email,
    }).execute()
    return {"ok": True}
