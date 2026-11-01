"""Supabase client factories.

- `service_client()` uses the SERVICE ROLE key and bypasses RLS. Used by the
  backend to perform server-clock-stamped, validated writes. NEVER exposed.
- All real authorization happens in FastAPI; RLS is a backstop for any direct
  (browser) access via the anon key.

If Supabase is not configured (local schema-only dev), these return None and
routers fall back to mock data so the app still boots.
"""
from functools import lru_cache
from typing import Optional

from .config import settings

try:
    from supabase import create_client, Client
except Exception:  # library optional at import time
    create_client = None
    Client = None  # type: ignore


@lru_cache
def service_client() -> Optional["Client"]:
    if not (create_client and settings.supabase_url and settings.supabase_service_role_key):
        return None
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def is_configured() -> bool:
    return service_client() is not None
