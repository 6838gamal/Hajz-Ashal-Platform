"""Module registration entrypoint. access_control has no HTTP routes of its
own yet (RBAC scaffolding only) - it exposes its models (for Alembic
autogenerate to see them) and its public_api/dependencies for other
modules to import."""
from __future__ import annotations

from fastapi import FastAPI

from modules.access_control.infrastructure import models  # noqa: F401  (registers ORM models with Base)


def register(app: FastAPI) -> None:
    pass
