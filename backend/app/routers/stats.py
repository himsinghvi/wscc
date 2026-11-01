"""Stats & charts (feature 5) — computed from match data, not hard-coded."""
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.auth import CurrentUser, get_current_user
from ..core.supabase_client import service_client
from ..core import sampledata as S
from ..services import analytics as A

router = APIRouter(prefix="/stats", tags=["stats"])


def _teams(sb):
    return S.TEAMS if sb is None else sb.table("teams").select("*").execute().data


def _matches(sb):
    return S.MATCHES if sb is None else sb.table("matches").select("*").execute().data


def _grounds(sb):
    return S.GROUNDS if sb is None else sb.table("grounds").select("*").execute().data


@router.get("/overview")
def overview(team_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    teams, matches, grounds = _teams(sb), _matches(sb), _grounds(sb)
    played = [m for m in matches if m.get("status") == "played"]

    focus = team_id or (user.team_id if getattr(user, "team_id", None) else None) or teams[0]["id"]
    return {
        "focus_team_id": focus,
        "totals": {
            "teams": len(teams),
            "grounds": len(grounds),
            "matches_played": len(played),
            "matches_scheduled": len([m for m in matches if m.get("status") == "scheduled"]),
        },
        "matches_by_month": A.matches_by_month(matches),
        "ground_usage": A.ground_usage(matches, grounds),
        "my_team_vs_others": A.team_vs_all(focus, teams, matches),
        "standings": A.standings(teams, matches),
    }


@router.get("/standings")
def standings(user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    return {"standings": A.standings(_teams(sb), _matches(sb))}


@router.get("/team/{team_id}")
def team_stats(team_id: str, user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    teams, matches = _teams(sb), _matches(sb)
    if not any(t["id"] == team_id for t in teams):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
    return {
        "team_id": team_id,
        "team": S.team_name(team_id),
        "record": A.team_record(team_id, matches),
        "vs_all": A.team_vs_all(team_id, teams, matches),
    }
