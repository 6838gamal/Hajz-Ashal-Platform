"""Standalone FastAPI application for the platform-owner admin panel.

This is a fully independent process from the tenant-facing app
(`app/main.py`): its own FastAPI instance, its own entrypoint, and its own
port. It shares the same codebase and the same database (via
`app.database`/`app.settings`) but does NOT run inside the tenant app's
process, so it can be started, restarted, and deployed to its own server
completely separately from the main booking app.

Run locally:
    uvicorn admin.main:app --host 0.0.0.0 --port 8000 --reload

Deploy separately: point a dedicated deployment/server at this module
(`admin.main:app`) with its own `DATABASE_URL`/`EXTERNAL_DATABASE_URL`,
`JWT_SECRET`, and `PLATFORM_ADMIN_TOKEN_TTL_MINUTES` env vars set to the same
values as the main app (they must share the JWT secret and the database to
work correctly, but nothing else is required from the main app's process).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.database import engine
from app.settings import get_settings
from core.presentation.error_handlers import register_error_handlers
from core.presentation.middlewares import RequestIdMiddleware
from admin.platform_admin.module import register as register_platform_admin

settings = get_settings()

app = FastAPI(title="لوحة تحكم مالك المنصة", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)

register_error_handlers(app)
register_platform_admin(app)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/admin/login")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready"}
