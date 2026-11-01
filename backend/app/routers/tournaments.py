"""Tournaments (feature 7) — details, polls, availability, fixtures, admins.

Permission model:
  * League admins (role == 'admin') can do everything, incl. create tournaments
    and appoint per-tournament admins.
  * A per-tournament admin (listed in a tournament's admin_player_ids) can edit
    that tournament, run polls and generate fixtures — but only for it.
  * Any authenticated user can read, vote in polls, and set their team's
    availability for a tournament their team is in.

Dev mode mutates the in-memory stores in sampledata; Supabase mode uses the
tournament_* tables. All authorization is enforced here on the server.
"""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core.supabase_client import service_client
from ..core import sampledata as S
from ..services import analytics as A
from ..services.scheduler import build_round_robin

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


# ---------- payloads ----------
class TournamentCreate(BaseModel):
    name: str
    description: str | None = None
    format: str = "league"
    start_date: str | None = None
    end_date: str | None = None
    team_ids: list[str] = []


class TournamentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    format: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    team_ids: list[str] | None = None
    status: str | None = None


class PollCreate(BaseModel):
    question: str
    options: list[str]
    closes_at: str | None = None


class PollVote(BaseModel):
    option_idx: int


class AvailabilitySet(BaseModel):
    available: bool


# ---------- helpers ----------
def _is_tadmin(user: CurrentUser, t: dict) -> bool:
    return user.is_admin or (user.player_id in (t.get("admin_player_ids") or []))


def _require_tadmin(user: CurrentUser, t: dict):
    if not _is_tadmin(user, t):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tournament admin only")


def _poll_payload(poll: dict, user: CurrentUser) -> dict:
    votes = S.POLL_VOTES.get(poll["id"], {})
    tally = [0] * len(poll["options"])
    for opt in votes.values():
        if 0 <= opt < len(tally):
            tally[opt] += 1
    return {**poll, "votes": tally, "total": sum(tally),
            "my_vote": votes.get(user.player_id)}


def _find(tid: str) -> dict:
    t = S.TOURNAMENTS_BY_ID.get(tid)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tournament not found")
    return t


# ---------- read ----------
@router.get("")
def list_tournaments(user: CurrentUser = Depends(get_current_user)):
    sb = service_client()
    if sb is not None:
        return {"tournaments": sb.table("tournaments").select("*").order("start_date", desc=True).execute().data}
    out = []
    for t in S.TOURNAMENTS:
        out.append({**t, "team_count": len(t["team_ids"]),
                    "is_admin": _is_tadmin(user, t)})
    return {"tournaments": out}


@router.get("/{tid}")
def get_tournament(tid: str, user: CurrentUser = Depends(get_current_user)):
    t = _find(tid)
    teams = [{"id": x, "name": S.team_name(x), "short": S.TEAMS_BY_ID.get(x, {}).get("short_name")}
             for x in t["team_ids"]]
    polls = [_poll_payload(p, user) for p in S.TOURNAMENT_POLLS if p["tournament_id"] == tid]
    avail = S.TOURN_AVAIL.get(tid, {})
    availability = [{"team_id": x["id"], "team": x["name"],
                     "available": avail.get(x["id"], {}).get("available")} for x in teams]
    admins = [{"player_id": pid, "name": _player_name(pid)} for pid in (t.get("admin_player_ids") or [])]
    fixtures = S.TOURNAMENT_FIXTURES.get(tid, [])
    my_team_in = user.team_id in t["team_ids"] if user.team_id else False
    return {
        "tournament": {k: v for k, v in t.items() if k != "admin_player_ids"},
        "teams": teams, "polls": polls, "availability": availability,
        "admins": admins, "fixtures": fixtures,
        "is_admin": _is_tadmin(user, t), "my_team_in": my_team_in,
    }


def _player_name(pid: str) -> str:
    # dev: map dev-ids via players sample; fallback to the id
    for p in S.PLAYERS:
        if p["id"] == pid:
            return p["full_name"]
    return {"dev-admin": "League Admin", "dev-rs": "Ravi Shah", "dev-tk": "Tarun Iyer",
            "dev-cc": "Chetan Nair"}.get(pid, pid)


# ---------- create / edit ----------
@router.post("", status_code=status.HTTP_201_CREATED)
def create_tournament(body: TournamentCreate, user: CurrentUser = Depends(require_admin)):
    sb = service_client()
    row = {"id": str(uuid.uuid4()), "name": body.name.strip(), "description": body.description,
           "format": body.format, "start_date": body.start_date, "end_date": body.end_date,
           "status": "draft", "team_ids": body.team_ids, "admin_player_ids": []}
    if not row["name"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Name required")
    if sb is None:
        S.TOURNAMENTS.append(row)
        S.TOURNAMENTS_BY_ID[row["id"]] = row
        S.TOURNAMENT_FIXTURES[row["id"]] = []
        return {"ok": True, "tournament": row}
    created = sb.table("tournaments").insert({
        "name": row["name"], "description": row["description"], "format": row["format"],
        "start_date": row["start_date"], "end_date": row["end_date"], "created_by": user.player_id,
    }).execute()
    return {"ok": True, "tournament": created.data[0]}


@router.put("/{tid}")
def update_tournament(tid: str, body: TournamentUpdate, user: CurrentUser = Depends(get_current_user)):
    t = _find(tid)
    _require_tadmin(user, t)
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    t.update(patch)
    return {"ok": True, "tournament": {k: v for k, v in t.items() if k != "admin_player_ids"}}


# ---------- admins (league admin only) ----------
@router.post("/{tid}/admins")
def add_tournament_admin(tid: str, player_id: str, user: CurrentUser = Depends(require_admin)):
    t = _find(tid)
    if player_id not in t["admin_player_ids"]:
        t["admin_player_ids"].append(player_id)
    sb = service_client()
    if sb is not None:
        sb.table("tournament_admins").upsert(
            {"tournament_id": tid, "player_id": player_id, "assigned_by": user.player_id}).execute()
    return {"ok": True, "admins": [{"player_id": p, "name": _player_name(p)} for p in t["admin_player_ids"]]}


@router.delete("/{tid}/admins/{player_id}")
def remove_tournament_admin(tid: str, player_id: str, user: CurrentUser = Depends(require_admin)):
    t = _find(tid)
    t["admin_player_ids"] = [p for p in t["admin_player_ids"] if p != player_id]
    return {"ok": True, "admins": [{"player_id": p, "name": _player_name(p)} for p in t["admin_player_ids"]]}


# ---------- polls ----------
@router.post("/{tid}/polls", status_code=status.HTTP_201_CREATED)
def create_poll(tid: str, body: PollCreate, user: CurrentUser = Depends(get_current_user)):
    t = _find(tid)
    _require_tadmin(user, t)
    if len(body.options) < 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provide at least two options")
    poll = {"id": str(uuid.uuid4()), "tournament_id": tid,
            "question": body.question.strip(), "options": body.options, "closes_at": body.closes_at}
    S.TOURNAMENT_POLLS.append(poll)
    S.POLL_VOTES[poll["id"]] = {}
    return {"ok": True, "poll": _poll_payload(poll, user)}


@router.post("/{tid}/polls/{poll_id}/vote")
def vote_poll(tid: str, poll_id: str, body: PollVote, user: CurrentUser = Depends(get_current_user)):
    _find(tid)
    poll = next((p for p in S.TOURNAMENT_POLLS if p["id"] == poll_id), None)
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Poll not found")
    if not (0 <= body.option_idx < len(poll["options"])):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid option")
    S.POLL_VOTES.setdefault(poll_id, {})[user.player_id] = body.option_idx
    return {"ok": True, "poll": _poll_payload(poll, user)}


# ---------- availability ----------
@router.post("/{tid}/availability")
def set_availability(tid: str, body: AvailabilitySet, user: CurrentUser = Depends(get_current_user)):
    t = _find(tid)
    if not user.team_id or user.team_id not in t["team_ids"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your team is not in this tournament")
    S.TOURN_AVAIL.setdefault(tid, {})[user.team_id] = {"available": body.available}
    return {"ok": True, "team_id": user.team_id, "available": body.available}


# ---------- fixtures (round-robin over participants) ----------
@router.post("/{tid}/fixtures/generate")
def generate_fixtures(tid: str, user: CurrentUser = Depends(get_current_user)):
    t = _find(tid)
    _require_tadmin(user, t)

    # Only teams marked available (default to all participants if none set).
    avail = S.TOURN_AVAIL.get(tid, {})
    team_ids = [x for x in t["team_ids"] if avail.get(x, {}).get("available", True)]
    if len(team_ids) < 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Need at least two available teams")

    h2h = A.head_to_head(S.MATCHES)
    counts = {tuple(sorted(k)): v for k, v in h2h.items()}
    grounds = [g["id"] for g in S.GROUNDS]
    result = build_round_robin(team_ids, counts, grounds,
                               {x: S.TEAMS_BY_ID.get(x, {}).get("home_ground_id") for x in team_ids})

    fixtures = []
    for i, p in enumerate(result.pairings, 1):
        fixtures.append({
            "id": f"{tid}-f{i}", "round": 1,
            "home_team_id": p.home_team_id, "home_team": S.team_name(p.home_team_id),
            "away_team_id": p.away_team_id, "away_team": S.team_name(p.away_team_id),
            "ground_id": p.ground_id, "ground": S.ground_name(p.ground_id),
            "met_before": p.meetings_so_far, "status": "scheduled",
        })
    S.TOURNAMENT_FIXTURES[tid] = fixtures
    return {"ok": True, "fixtures": fixtures,
            "byes": [S.team_name(b) for b in result.byes],
            "fairness_score": result.fairness_score}
