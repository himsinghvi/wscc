"""Dev/test-only automation: create a live poll, vote on behalf of every test
team with random dates, and optionally auto-build the schedule.

Guarded to offline dev mode (no Supabase) + admin, so it can never run against
a real backend.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core.auth import CurrentUser, require_admin
from ..core.supabase_client import is_configured
from ..core.time_windows import now as tz_now
from ..core import sampledata as S
from ..schemas import ScheduleRequest, ApplyScheduleRequest
from ..services import poll_schedule as sched
from ..services.config_service import window_config
from . import availability as av
from . import scheduler as sch

router = APIRouter(prefix="/dev", tags=["dev"])


class SimulateRequest(BaseModel):
    num_teams: int = 12
    dates: list[str] | None = None       # default: next Sat + Sun
    slots: list[str] | None = None       # default: 1st / 2nd
    generate_schedule: bool = True
    early_fraction: float = 0.15         # some teams vote "early" (shown red)


def _default_dates(today: date) -> list[str]:
    sat = today + timedelta(days=(5 - today.weekday()) % 7)
    sun = sat + timedelta(days=1)
    return [sat.isoformat(), sun.isoformat()]


@router.post("/simulate")
def simulate(body: SimulateRequest, user: CurrentUser = Depends(require_admin)):
    if is_configured():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Simulation is available in dev mode only.")

    cfg = window_config()
    now = tz_now(cfg)

    # 1) fresh state: clear scheduled polls + the in-memory availability store
    sched._POLLS.clear(); sched._save()
    av._DEV_STORE.clear()

    dates = sorted(body.dates or _default_dates(now.date()))
    slots = body.slots or ["1st", "2nd"]

    # 2) create a poll that is OPEN right now (opened 2h ago; publish still ahead)
    open_dt = now - timedelta(hours=2)
    poll = sched.create_poll(cfg, label="Simulated weekend poll",
                             vote_open_at=open_dt.isoformat(), dates=dates, slots=slots,
                             created_by=user.player_id)
    w, meta = sched.effective_windows(cfg, now)
    poll_dates = meta["dates"]
    wk = w.weekend_date.isoformat()

    # 3) vote on behalf of each test team with a RANDOM set of dates
    accts = S.dev_accounts(body.num_teams)[1:]  # skip the admin account
    offsets = random.sample(range(1, 1 + max(len(accts) * 5, len(accts))), len(accts))
    voters = []
    for a, off in zip(accts, offsets):
        k = random.randint(1, len(poll_dates))
        chosen = sorted(random.sample(poll_dates, k))
        tokens = av._all_tokens(chosen, slots)

        early = random.random() < body.early_fraction
        if early:
            ts = w.vote_open_at - timedelta(minutes=random.randint(1, 40))
        else:
            ts = w.vote_open_at + timedelta(seconds=off, milliseconds=random.randint(0, 999))

        av._DEV_STORE.setdefault(wk, []).append({
            "team_id": a["team_id"], "submitted_by": a["player_id"],
            "submitted_at": ts.isoformat(), "submitted_at_ms": av._ms(ts),
            "status": "available", "is_early": early,
            "available_slots": tokens, "available_dates": chosen,
            "note": None,
        })
        voters.append({"team": a["team"], "dates": chosen, "early": early})

    # 4) optionally auto-build + apply a schedule for each date
    created = 0
    schedule = []
    if body.generate_schedule:
        for d in poll_dates:
            g = sch.generate(ScheduleRequest(date=d), user)
            if g.get("fixtures"):
                sch.apply(ApplyScheduleRequest(fixtures=g["fixtures"]), user)
                created += len(g["fixtures"])
                schedule.append({"date": d, "fixtures": len(g["fixtures"])})

    return {
        "ok": True,
        "poll": {"label": poll["label"], "dates": poll_dates, "slots": slots,
                 "vote_open_at": poll["vote_open_at"], "publish_at": poll["publish_at"],
                 "backout_close_at": poll["backout_close_at"]},
        "voted_teams": len(voters),
        "voters": voters,
        "matches_created": created,
        "schedule": schedule,
    }


@router.post("/reset")
def reset(user: CurrentUser = Depends(require_admin)):
    """Clear simulated polls + in-memory availability (dev mode only)."""
    if is_configured():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dev mode only.")
    sched._POLLS.clear(); sched._save()
    av._DEV_STORE.clear()
    return {"ok": True}
