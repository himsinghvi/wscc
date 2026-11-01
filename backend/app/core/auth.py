"""Authentication & authorization dependencies.

Verifies the Supabase user JWT on every request and resolves the caller to a
player record (team + role). In local/schema-only dev (no Supabase configured)
a dev-mode header `X-Dev-Email` is accepted so the UI is explorable offline.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings
from .supabase_client import service_client, is_configured


@dataclass
class CurrentUser:
    auth_user_id: Optional[str]
    email: str
    player_id: Optional[str]
    team_id: Optional[str]
    role: str = "player"
    is_rep: bool = False

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@lru_cache
def _jwk_client() -> "jwt.PyJWKClient":
    # Supabase publishes its asymmetric signing keys here.
    return jwt.PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


def _decode_jwt(token: str) -> dict:
    """Verify a Supabase user JWT.

    - If a legacy HS256 shared secret is configured, verify with it.
    - Otherwise verify against the project's JWKS (modern ES256/RS256 keys).
    """
    opts = {"verify_aud": False}  # Supabase aud = "authenticated"
    try:
        if settings.supabase_jwt_secret:
            return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], options=opts)
        if settings.supabase_url:
            key = _jwk_client().get_signing_key_from_jwt(token).key
            return jwt.decode(token, key, algorithms=["ES256", "RS256"], options=opts)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")
    except Exception as e:  # JWKS fetch / key errors
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token verification failed: {e}")
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Auth not configured")


def _lookup_player(email: str, auth_user_id: Optional[str]) -> CurrentUser:
    sb = service_client()
    if sb is None:
        # dev fallback: resolve from the generated test accounts so the full
        # voting flow is demoable without Supabase. Unknown emails → admin.
        from . import sampledata as S
        a = S.dev_account_for(email)
        if a:
            return CurrentUser(auth_user_id=auth_user_id, email=email, player_id=a["player_id"],
                               team_id=a["team_id"], role=a["role"], is_rep=(a["role"] != "player"))
        return CurrentUser(auth_user_id=auth_user_id, email=email, player_id="dev-admin",
                           team_id=(S.TEAMS[0]["id"] if S.TEAMS else None), role="admin", is_rep=True)

    # allow-list check (feature 1) — authoritative on the server
    allowed = sb.table("allowed_emails").select("*").eq("email", email).eq("is_active", True).execute()
    if not allowed.data:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email not allow-listed")

    player = sb.table("players").select("*").eq("email", email).execute()
    if player.data:
        p = player.data[0]
        # link auth_user_id on first sign-in
        if auth_user_id and not p.get("auth_user_id"):
            sb.table("players").update({"auth_user_id": auth_user_id}).eq("id", p["id"]).execute()
        return CurrentUser(auth_user_id=auth_user_id, email=email, player_id=p["id"],
                           team_id=p.get("team_id"), role=p.get("role", "player"),
                           is_rep=p.get("is_rep", False))
    # create a player row from allow-list entry
    a = allowed.data[0]
    created = sb.table("players").insert({
        "email": email, "auth_user_id": auth_user_id,
        "team_id": a.get("team_id"), "role": a.get("role", "player"),
    }).execute()
    p = created.data[0]
    return CurrentUser(auth_user_id=auth_user_id, email=email, player_id=p["id"],
                       team_id=p.get("team_id"), role=p.get("role", "player"))


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_dev_email: Optional[str] = Header(None),
) -> CurrentUser:
    # Dev mode: no Supabase → trust X-Dev-Email so the app is explorable.
    if not is_configured():
        return _lookup_player(x_dev_email or "admin@wscc.app", auth_user_id=None)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    claims = _decode_jwt(token)
    email = claims.get("email") or claims.get("user_metadata", {}).get("email")
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has no email")
    return _lookup_player(email, auth_user_id=claims.get("sub"))


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
