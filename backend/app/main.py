"""WSCC FastAPI application factory.

Single-origin design: the API is served under `/api/*` and (when a built
frontend exists) the React SPA is served from the same app — so one port /
one domain serves everything, locally and on Vercel.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .core.config import settings
from .core.supabase_client import is_configured
from .routers import (
    availability, admin, teams, grounds, matches, stats,
    tournaments, scheduler, directory, sessions, meta, day_rules, polls, dev, signup,
)

app = FastAPI(
    title="WSCC — Weekend Cricket League API",
    version="0.1.0",
    description="Server-authoritative API for availability voting, rankings, "
                "backout windows, scheduling and tournaments.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "env": settings.env, "supabase_configured": is_configured()}


# All feature routers live under /api so they never collide with SPA routes.
for r in (meta, sessions, availability, teams, grounds, matches, stats,
          tournaments, scheduler, directory, admin, day_rules, polls, dev, signup):
    app.include_router(r.router, prefix="/api")


# ---- Serve the built frontend from the same origin (single port) ----
# repo-root/frontend/dist  (parents[2] = repo root from backend/app/main.py)
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.exists():
    # hashed assets + PWA files are real files; everything else falls back to
    # index.html so client-side routes (e.g. /teams/:id) work on refresh.
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            return FileResponse(_DIST / "index.html", status_code=404)
        candidate = _DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
