from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AvailabilitySubmit(BaseModel):
    note: Optional[str] = None  # the client sends NO timestamp — server stamps it
    available_dates: Optional[list[str]] = None   # whole-day availability (expands to all slots)
    available_slots: Optional[list[str]] = None   # "YYYY-MM-DD#slot" tokens (per date+slot)


class BackoutRequest(BaseModel):
    reason: Optional[str] = None
    dates: Optional[list[str]] = None   # back out of whole days (all their slots)
    slots: Optional[list[str]] = None   # back out of specific "date#slot" tokens


class ConfigUpdate(BaseModel):
    timezone: Optional[str] = None
    vote_open_time: Optional[str] = None
    publish_time: Optional[str] = None
    backout_weekday: Optional[int] = None
    backout_close_time: Optional[str] = None
    max_voting_teams: Optional[int] = None
    max_sessions_per_team: Optional[int] = None
    session_policy: Optional[str] = None
    reject_early_votes: Optional[bool] = None


class SessionRegister(BaseModel):
    jti: str
    user_agent: Optional[str] = None


class RankingRow(BaseModel):
    rank: Optional[int]
    team_id: str
    team_name: str
    submitted_at: datetime
    submitted_at_ms: int
    is_early: bool
    status: str
    color: str  # "red" | "green"


class ScheduleRequest(BaseModel):
    team_ids: Optional[list[str]] = None        # explicit set; defaults to available teams
    exclude_team_ids: Optional[list[str]] = None  # what-if: drop these teams
    ground_rotation: str = "balanced"           # "balanced" | "home"
    day: Optional[str] = None                   # (legacy) MON..SUN
    date: Optional[str] = None                  # a specific polled match date (ISO)


class ApplyScheduleRequest(BaseModel):
    # Persist the given (or last-generated) fixtures as scheduled matches.
    fixtures: Optional[list[dict]] = None
