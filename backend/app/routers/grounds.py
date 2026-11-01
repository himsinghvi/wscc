"""Grounds (feature 5) — list + detail (matches hosted, usage).

Admins can create and edit grounds; validation is server-side.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core.supabase_client import service_client
from ..core import sampledata as S

router = APIRouter(prefix="/grounds", tags=["grounds"])


class GroundCreate(BaseModel):
    name: str
    city: str | None = None
    pitch_type: str | None = "turf"
    address: str | None = None
    notes: str | None = None
    lat: float | None = None
    lng: float | None = None

    @field_validator("name")
    @classmethod
    def _nonblank(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("name must not be blank")
        return v


class GroundUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    pitch_type: str | None = None
    address: str | None = None
    notes: str | None = None
    lat: float | None = None
    lng: float | None = None


def _grounds(sb):
    return S.GROUNDS if sb is None else sb.table("grounds").select("*").order("name").execute().data


def _matches(sb):
    return S.MATCHES if sb is None else sb.table("matches").select("*").execute().data


@router.get("")
def list_grounds(user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    grounds = _grounds(sb)
    matches = _matches(sb)
    for g in grounds:
        g["match_count"] = sum(1 for m in matches if m.get("ground_id") == g["id"])
    return {"grounds": grounds}


@router.get("/{ground_id}")
def get_ground(ground_id: str, user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    ground = next((g for g in _grounds(sb) if g["id"] == ground_id), None)
    if not ground:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ground not found")

    all_teams = S.TEAMS if sb is None else sb.table("teams").select("id,name,home_ground_id").execute().data
    tname = {t["id"]: t["name"] for t in all_teams}

    here = [m for m in _matches(sb) if m.get("ground_id") == ground_id]
    for m in here:
        m["home_team"] = tname.get(m["home_team_id"], m["home_team_id"])
        m["away_team"] = tname.get(m["away_team_id"], m["away_team_id"])
    here.sort(key=lambda m: m.get("scheduled_at", ""), reverse=True)

    home_teams = [t for t in all_teams if t.get("home_ground_id") == ground_id]
    return {"ground": ground, "matches": here, "match_count": len(here),
            "home_teams": [t["name"] for t in home_teams]}


def _dupe_name(grounds, name: str, exclude_id: str | None = None) -> bool:
    low = name.strip().lower()
    return any(g["name"].strip().lower() == low and g["id"] != exclude_id for g in grounds)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ground(body: GroundCreate, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    grounds = _grounds(sb)
    if _dupe_name(grounds, body.name):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A ground named '{body.name}' already exists")

    row = body.model_dump()
    if sb is None:
        row["id"] = str(uuid.uuid4())
        S.GROUNDS.append(row)
        S.GROUNDS_BY_ID[row["id"]] = row
        return {"ok": True, "ground": row}
    created = sb.table("grounds").insert(row).execute()
    sb.table("audit_log").insert({"actor_id": user.player_id, "action": "ground.create",
                                  "entity": "grounds", "entity_id": created.data[0]["id"]}).execute()
    return {"ok": True, "ground": created.data[0]}


@router.put("/{ground_id}")
def update_ground(ground_id: str, body: GroundUpdate, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    grounds = _grounds(sb)
    ground = next((g for g in grounds if g["id"] == ground_id), None)
    if not ground:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ground not found")
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if "name" in patch and _dupe_name(grounds, patch["name"], exclude_id=ground_id):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A ground named '{patch['name']}' already exists")

    if sb is None:
        ground.update(patch)
        return {"ok": True, "ground": ground}
    sb.table("grounds").update(patch).eq("id", ground_id).execute()
    return {"ok": True}
