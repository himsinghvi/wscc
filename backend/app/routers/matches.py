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


def _decorate(m):
    return {**m, "home_team": S.team_name(m["home_team_id"]),
            "away_team": S.team_name(m["away_team_id"]),
            "ground": S.ground_name(m.get("ground_id"))}


@router.get("")
def list_matches(status: str | None = None, team_id: str | None = None,
                 user: CurrentUser = Depends(get_current_user)):
    data = _matches(service_client())
    if status:
        data = [m for m in data if m.get("status") == status]
    if team_id:
        data = [m for m in data if team_id in (m["home_team_id"], m["away_team_id"])]
    data = sorted(data, key=lambda m: m.get("scheduled_at", ""), reverse=True)
    return {"matches": [_decorate(m) for m in data]}


@router.get("/head-to-head")
def head_to_head(user: CurrentUser = Depends(get_current_user)):
    counts = A.head_to_head(_matches(service_client()))
    return {"head_to_head": [
        {"pair": list(k), "pair_names": [S.team_name(k[0]), S.team_name(k[1])], "played": v}
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    ]}


@router.post("/schedule")
def schedule_match(body: ScheduleMatch, user: CurrentUser = Depends(require_admin)):
    if body.home_team_id == body.away_team_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A team can't play itself")
    sb = service_client()
    row = {**body.model_dump(), "status": "scheduled"}
    if sb is None:
        row["id"] = f"m{len(S.MATCHES) + 1:02d}"
        S.MATCHES.append(row)
        return {"ok": True, "match": _decorate(row)}
    created = sb.table("matches").insert(row).execute()
    return {"ok": True, "match": _decorate(created.data[0])}


@router.put("/{match_id}/result")
def record_result(match_id: str, body: RecordResult, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    patch = {**body.model_dump(), "status": "played"}
    if sb is None:
        m = next((x for x in S.MATCHES if x["id"] == match_id), None)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Match not found")
        m.update(patch)
        return {"ok": True, "match": _decorate(m)}
    sb.table("matches").update(patch).eq("id", match_id).execute()
    return {"ok": True}
