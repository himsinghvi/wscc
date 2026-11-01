"""Day-availability rules (feature: temporarily disable entities for scheduling).

Admins can mark a ground / team / player as unavailable on specific weekdays
(MON..SUN) or ANY. The scheduler excludes disabled entities for the target day.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core.auth import CurrentUser, get_current_user, require_admin
from ..core import sampledata as S

router = APIRouter(prefix="/day-rules", tags=["day-rules"])


class DayRuleSet(BaseModel):
    entity_type: str          # ground | team | player
    entity_id: str
    days: list[str]           # subset of MON..SUN, or ["ANY"], or [] to clear


class BulkItem(BaseModel):
    entity_id: str
    days: list[str]


class BulkSet(BaseModel):
    entity_type: str
    items: list[BulkItem]     # per-entity target day lists (computed by the client)


@router.get("")
def get_rules(user: CurrentUser = Depends(get_current_user)):
    """Current rules + the weekday vocabulary (so the UI can render toggles)."""
    return {"weekdays": S.WEEKDAYS, "entity_types": list(S.ENTITY_TYPES), "rules": S.day_rules_map()}


@router.put("")
def set_rule(body: DayRuleSet, user: CurrentUser = Depends(require_admin)):
    if body.entity_type not in S.ENTITY_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"entity_type must be one of {S.ENTITY_TYPES}")
    bad = [d for d in body.days if d not in S.WEEKDAYS and d != "ANY"]
    if bad:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid days: {bad}")
    applied = S.set_day_rule(body.entity_type, body.entity_id, body.days)
    return {"ok": True, "entity_type": body.entity_type, "entity_id": body.entity_id, "days": applied}


@router.put("/bulk")
def bulk_set(body: BulkSet, user: CurrentUser = Depends(require_admin)):
    """Apply day lists to many entities at once (select/unselect all)."""
    if body.entity_type not in S.ENTITY_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"entity_type must be one of {S.ENTITY_TYPES}")
    for it in body.items:
        bad = [d for d in it.days if d not in S.WEEKDAYS and d != "ANY"]
        if bad:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"invalid days: {bad}")
        S.set_day_rule(body.entity_type, it.entity_id, it.days)
    return {"ok": True, "entity_type": body.entity_type, "count": len(body.items),
            "rules": S.DAY_RULES[body.entity_type]}
