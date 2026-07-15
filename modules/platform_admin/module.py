from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from modules.platform_admin.infrastructure import models  # noqa: F401
from modules.platform_admin.presentation.routers import router as api_router
from modules.platform_admin.presentation.web_routes import router as web_router


def register(app: FastAPI) -> None:
    app.include_router(api_router)
    app.include_router(web_router)
    app.mount("/admin/static", StaticFiles(directory="admin/static"), name="admin_static")
