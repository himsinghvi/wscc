"""Matches + head-to-head (feature 5). Admins can schedule and record results."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core.supabase_client import service_client
from ..core import sampledata as S
from ..services import analytics as A

router = APIRouter(prefix="/matches", tags=["matches"])

# Back-compat alias used by the scheduler fallback.
_MOCK_MATCHES = S.MATCHES


class ScheduleMatch(BaseModel):
    home_team_id: str
    away_team_id: str
    ground_id: str | None = None
    scheduled_at: str | None = None


class RecordResult(BaseModel):
    home_score: str
    away_score: str
    winner_id: str
    result: str


def _matches(sb):
    return S.MATCHES if sb is None else sb.table("matches").select("*").order("scheduled_at", desc=True).execute().data


def _name_maps(sb):
    """team_id->name and ground_id->name, from the DB (Supabase) or sample data."""
    if sb is None:
        return ({t["id"]: t["name"] for t in S.TEAMS}, {g["id"]: g["name"] for g in S.GROUNDS})
    tn = {t["id"]: t["name"] for t in sb.table("teams").select("id,name").execute().data}
    gn = {g["id"]: g["name"] for g in sb.table("grounds").select("id,name").execute().data}
    return tn, gn


def _decorate(m, tn, gn):
    return {**m, "home_team": tn.get(m["home_team_id"], m["home_team_id"]),
            "away_team": tn.get(m["away_team_id"], m["away_team_id"]),
            "ground": gn.get(m.get("ground_id"))}


@router.get("")
def list_matches(status: str | None = None, team_id: str | None = None,
                 user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    tn, gn = _name_maps(sb)
    data = _matches(sb)
    if status:
        data = [m for m in data if m.get("status") == status]
    if team_id:
        data = [m for m in data if team_id in (m["home_team_id"], m["away_team_id"])]
    data = sorted(data, key=lambda m: m.get("scheduled_at", ""), reverse=True)
    return {"matches": [_decorate(m, tn, gn) for m in data]}


@router.get("/head-to-head")
def head_to_head(user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    tn, _ = _name_maps(sb)
    counts = A.head_to_head(_matches(sb))
    return {"head_to_head": [
        {"pair": list(k), "pair_names": [tn.get(k[0], k[0]), tn.get(k[1], k[1])], "played": v}
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    ]}


@router.post("/schedule")
def schedule_match(body: ScheduleMatch, user: CurrentUser = Depends(require_admin)):
    if body.home_team_id == body.away_team_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A team can't play itself")
    sb = service_client()
    tn, gn = _name_maps(sb)
    row = {**body.model_dump(), "status": "scheduled"}
    if sb is None:
        row["id"] = f"m{len(S.MATCHES) + 1:02d}"
        S.MATCHES.append(row)
        return {"ok": True, "match": _decorate(row, tn, gn)}
    created = sb.table("matches").insert(row).execute()
    return {"ok": True, "match": _decorate(created.data[0], tn, gn)}


@router.put("/{match_id}/result")
def record_result(match_id: str, body: RecordResult, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    patch = {**body.model_dump(), "status": "played"}
    if sb is None:
        m = next((x for x in S.MATCHES if x["id"] == match_id), None)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")
        m.update(patch)
        tn, gn = _name_maps(sb)
        return {"ok": True, "match": _decorate(m, tn, gn)}
    sb.table("matches").update(patch).eq("id", match_id).execute()
    return {"ok": True}
