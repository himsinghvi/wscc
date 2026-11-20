"""Admin configuration (features 4 & 6) — admin-only, audited."""
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import CurrentUser, require_admin
from ..core.supabase_client import service_client
from ..core import sampledata as S
from ..schemas import ConfigUpdate
from ..services.config_service import load_config

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/members")
def members(user: CurrentUser = Depends(require_admin)):
    """All registered users: approved members, pending requests, and anyone who
    created a login. Passwords are never stored in readable form, so they cannot
    be (and are not) returned."""
    sb = service_client()
    if sb is None:
        rows = [{"email": p.get("email") or f"{p['id']}@dev", "full_name": p["full_name"],
                 "team": S.team_name(p["team_id"]), "role": p["role"], "status": "approved",
                 "phone": p.get("phone"), "last_sign_in": None} for p in S.PLAYERS]
        return {"members": rows, "count": len(rows)}

    teams = {t["id"]: t["name"] for t in sb.table("teams").select("id,name").execute().data}
    allowed = {a["email"]: a for a in sb.table("allowed_emails").select("email,role,is_active,team_id").execute().data}
    players = {p["email"]: p for p in sb.table("players").select("email,full_name,phone,whatsapp,team_id,role").execute().data if p.get("email")}
    reqs = {r["email"]: r for r in sb.table("signup_requests").select("email,full_name,team_id,status,created_at").execute().data}

    last_seen, created = {}, {}
    try:  # auth users give last-sign-in + catch logins without an app record
        res = sb.auth.admin.list_users()
        auth_users = res if isinstance(res, list) else getattr(res, "users", []) or []
        for u in auth_users:
            em = (getattr(u, "email", None) or "").lower()
            if em:
                last_seen[em] = getattr(u, "last_sign_in_at", None)
                created[em] = getattr(u, "created_at", None)
    except Exception:
        auth_users = []

    emails = set(allowed) | set(reqs) | set(last_seen)
    out = []
    for e in emails:
        a = allowed.get(e); r = reqs.get(e); p = players.get(e, {})
        if a and a.get("is_active"):
            status_ = "admin" if a.get("role") == "admin" else "approved"
            team_id = a.get("team_id"); role = a.get("role")
        elif r:
            status_ = r.get("status"); team_id = r.get("team_id"); role = "team_rep"
        else:
            status_ = "registered"; team_id = None; role = None
        out.append({
            "email": e, "full_name": p.get("full_name") or (r or {}).get("full_name"),
            "team": teams.get(team_id, None), "role": role, "status": status_,
            "phone": p.get("phone"), "whatsapp": p.get("whatsapp"),
            "last_sign_in": last_seen.get(e.lower()), "created_at": created.get(e.lower()) or (r or {}).get("created_at"),
        })
    out.sort(key=lambda x: (x["status"] != "admin", x["team"] or "zzz", x["email"]))
    return {"members": out, "count": len(out)}


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
