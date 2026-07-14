from __future__ import annotations

from fastapi import FastAPI

from modules.tenants.infrastructure import models  # noqa: F401
from modules.tenants.presentation.routers import router


def register(app: FastAPI) -> None:
    app.include_router(router)
