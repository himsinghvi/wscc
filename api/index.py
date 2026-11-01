"""Vercel Python serverless entry point.

Vercel routes every /api/* request here; it detects the module-level ASGI
`app` (FastAPI). The backend package lives in ../backend and is bundled via
vercel.json `includeFiles`.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402  (exposed for Vercel's ASGI runtime)
