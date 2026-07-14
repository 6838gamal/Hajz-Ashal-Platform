from __future__ import annotations

from fastapi import FastAPI

from modules.identity.infrastructure import models  # noqa: F401
from modules.identity.presentation.routers import router


def register(app: FastAPI) -> None:
    app.include_router(router)
