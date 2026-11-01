"""Team-rep directory (feature 9) — 1-click phone / WhatsApp."""
from fastapi import APIRouter, Depends
from ..core.auth import CurrentUser, get_current_user
from ..core.supabase_client import service_client
from ..core import sampledata as S

router = APIRouter(prefix="/directory", tags=["directory"])


@router.get("")
def directory(reps_only: bool = True, user: CurrentUser = Depends(get_current_user)):
    """Returns players with click-to-call / WhatsApp deep links the UI renders as buttons."""
    sb = service_client()
    if sb is None:
        src = [p for p in S.PLAYERS if (p["is_rep"] or not reps_only)]
        people = [{"player_id": p["id"], "team": S.team_name(p["team_id"]), "name": p["full_name"],
                   "phone": p["phone"], "whatsapp": p["whatsapp"], "role": p["role"],
                   "is_rep": p["is_rep"]} for p in src]
    else:
        q = sb.table("players").select("id,full_name,phone,whatsapp,role,is_rep,teams(name)")
        if reps_only:
            q = q.eq("is_rep", True)
        rows = q.execute().data
        people = [{"player_id": r.get("id"), "team": (r.get("teams") or {}).get("name"),
                   "name": r.get("full_name"), "phone": r.get("phone"), "whatsapp": r.get("whatsapp"),
                   "role": r.get("role"), "is_rep": r.get("is_rep")}
                  for r in rows]
    for p in people:
        wa = (p.get("whatsapp") or "").replace("+", "").replace(" ", "")
        p["whatsapp_link"] = f"https://wa.me/{wa}" if wa else None
        p["call_link"] = f"tel:{p.get('phone')}" if p.get("phone") else None
    return {"directory": people}
