"""Admin-scheduled poll rounds (schedule availability polling at a date/time)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..services import poll_schedule as sched
from ..services.config_service import window_config
from ..core.time_windows import now as tz_now

router = APIRouter(prefix="/poll-schedule", tags=["poll-schedule"])


class PollCreate(BaseModel):
    label: str | None = None
    vote_open_at: str                 # ISO; naive is interpreted in app timezone
    publish_at: str | None = None     # default: open + 6h
    backout_close_at: str | None = None  # default: open + 3 days
    weekend_date: str | None = None   # default: first date / next Saturday
    dates: list[str] | None = None    # the dates availability is collected for
    slots: list[str] | None = None    # time-slots per day (default 1st / 2nd)


class PollEdit(BaseModel):
    label: str | None = None
    vote_open_at: str | None = None
    publish_at: str | None = None
    backout_close_at: str | None = None
    weekend_date: str | None = None
    dates: list[str] | None = None
    slots: list[str] | None = None


@router.get("")
def list_scheduled(user: CurrentUser = Depends(get_current_user)):
    cfg = window_config()
    now = tz_now(cfg)
    current = sched.current_scheduled(cfg, now)
    polls = []
    for p in sched.list_polls():
        o = sched._parse(p["vote_open_at"], cfg)
        b = sched._parse(p["backout_close_at"], cfg)
        state = "live" if o <= now < b else ("upcoming" if now < o else "past")
        polls.append({**p, "state": state, "is_current": bool(current and current["id"] == p["id"])})
    return {"polls": polls, "timezone": cfg.timezone,
            "current_poll_id": current["id"] if current else None}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_scheduled(body: PollCreate, user: CurrentUser = Depends(require_admin)):
    cfg = window_config()
    try:
        poll = sched.create_poll(
            cfg, label=body.label, vote_open_at=body.vote_open_at,
            publish_at=body.publish_at, backout_close_at=body.backout_close_at,
            weekend_date=body.weekend_date, dates=body.dates, slots=body.slots,
            created_by=user.player_id,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"ok": True, "poll": poll}


@router.put("/{poll_id}")
def edit_scheduled(poll_id: str, body: PollEdit, user: CurrentUser = Depends(require_admin)):
    cfg = window_config()
    try:
        poll = sched.update_poll(cfg, poll_id, **body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    if not poll:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheduled poll not found")
    return {"ok": True, "poll": poll}


@router.delete("/{poll_id}")
def delete_scheduled(poll_id: str, user: CurrentUser = Depends(require_admin)):
    if not sched.delete_poll(poll_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheduled poll not found")
    return {"ok": True}
