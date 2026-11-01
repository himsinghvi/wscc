"""Teams (feature 5) — list + rich detail (roster, record, form, H2H).

Admins can create and edit teams; validation is server-side.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core.supabase_client import service_client
from ..core import sampledata as S
from ..services import analytics as A

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamCreate(BaseModel):
    name: str
    short_name: str
    home_ground_id: str | None = None
    color: str | None = "#4f8cff"

    @field_validator("name", "short_name")
    @classmethod
    def _nonblank(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class TeamUpdate(BaseModel):
    name: str | None = None
    short_name: str | None = None
    home_ground_id: str | None = None
    color: str | None = None

# Back-compat alias used elsewhere (e.g. scheduler fallback).
_MOCK_TEAMS = S.TEAMS


def _teams(sb):
    return S.TEAMS if sb is None else sb.table("teams").select("*").order("name").execute().data


def _matches(sb):
    return S.MATCHES if sb is None else sb.table("matches").select("*").execute().data


@router.get("")
def list_teams(user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    teams = _teams(sb)
    matches = _matches(sb)
    # attach a quick record so the grid can show form without N calls
    enriched = []
    for t in teams:
        rec = A.team_record(t["id"], matches)
        enriched.append({**t, "record": rec})
    return {"teams": enriched}


@router.get("/{team_id}")
def get_team(team_id: str, user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    teams = _teams(sb)
    team = next((t for t in teams if t["id"] == team_id), None)
    if not team:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")

    matches = _matches(sb)
    roster = ([p for p in S.PLAYERS if p["team_id"] == team_id] if sb is None
              else sb.table("players").select("*").eq("team_id", team_id).execute().data)

    recent = sorted(
        [m for m in matches if team_id in (m["home_team_id"], m["away_team_id"])],
        key=lambda m: m.get("scheduled_at", ""), reverse=True,
    )[:6]
    for m in recent:
        m = m  # annotate names for the UI
        m["home_team"] = S.team_name(m["home_team_id"])
        m["away_team"] = S.team_name(m["away_team_id"])
        m["ground"] = S.ground_name(m.get("ground_id"))

    return {
        "team": team,
        "home_ground": S.GROUNDS_BY_ID.get(team.get("home_ground_id")),
        "record": A.team_record(team_id, matches),
        "vs_all": A.team_vs_all(team_id, teams, matches),
        "roster": roster,
        "recent_matches": recent,
    }


def _dupe_name(teams, name: str, exclude_id: str | None = None) -> bool:
    low = name.strip().lower()
    return any(t["name"].strip().lower() == low and t["id"] != exclude_id for t in teams)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(body: TeamCreate, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    teams = _teams(sb)
    if _dupe_name(teams, body.name):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A team named '{body.name}' already exists")

    row = {"name": body.name, "short_name": body.short_name,
           "home_ground_id": body.home_ground_id or None, "color": body.color or "#4f8cff"}
    if sb is None:
        row["id"] = str(uuid.uuid4())
        S.TEAMS.append(row)
        S.TEAMS_BY_ID[row["id"]] = row
        return {"ok": True, "team": row}
    created = sb.table("teams").insert(row).execute()
    sb.table("audit_log").insert({"actor_id": user.player_id, "action": "team.create",
                                  "entity": "teams", "entity_id": created.data[0]["id"]}).execute()
    return {"ok": True, "team": created.data[0]}


@router.put("/{team_id}")
def update_team(team_id: str, body: TeamUpdate, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    teams = _teams(sb)
    team = next((t for t in teams if t["id"] == team_id), None)
    if not team:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if "name" in patch and _dupe_name(teams, patch["name"], exclude_id=team_id):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A team named '{patch['name']}' already exists")

    if sb is None:
        team.update(patch)
        return {"ok": True, "team": team}
    sb.table("teams").update(patch).eq("id", team_id).execute()
    return {"ok": True}
