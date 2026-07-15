"""Central configuration. All values come from environment variables -
nothing is hardcoded. Modules may add their own ModuleSettings and import
this Settings object; they must not read os.environ directly."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _to_asyncpg_url(url: str) -> str:
    """asyncpg doesn't accept psycopg2-style `sslmode=` query params, so we
    strip it. Replit's local Postgres uses `sslmode=disable`, which maps to
    simply not passing an ssl context (asyncpg's default)."""
    if url.startswith("postgresql+asyncpg://"):
        base = url
    elif url.startswith("postgresql://"):
        base = "postgresql+asyncpg://" + url[len("postgresql://"):]
    else:
        base = url

    if "?" in base:
        head, query = base.split("?", 1)
        kept = [p for p in query.split("&") if p and not p.startswith("sslmode=")]
        base = head + ("?" + "&".join(kept) if kept else "")
    return base


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql://postgres:password@localhost/app"

    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30

    # Platform-admin sessions are separate from tenant sessions (no refresh
    # rotation yet - single long-lived access token), hence the longer TTL.
    platform_admin_token_ttl_minutes: int = 480

    cors_origins: str = "*"
    log_level: str = "info"

    @property
    def async_database_url(self) -> str:
        return _to_asyncpg_url(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    import os

    # EXTERNAL_DATABASE_URL (Render Postgres) is the single source of truth
    # for the database connection, per explicit user decision. It takes
    # priority over Replit's runtime-managed DATABASE_URL.
    database_url = os.environ.get("EXTERNAL_DATABASE_URL") or os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost/app"
    )

    return Settings(
        environment=os.environ.get("ENVIRONMENT", "development"),
        database_url=database_url,
        jwt_secret=os.environ.get("JWT_SECRET", os.environ.get("SESSION_SECRET", "dev-only-insecure-secret-change-me")),
        jwt_access_ttl_minutes=int(os.environ.get("JWT_ACCESS_TTL_MINUTES", "15")),
        jwt_refresh_ttl_days=int(os.environ.get("JWT_REFRESH_TTL_DAYS", "30")),
        platform_admin_token_ttl_minutes=int(os.environ.get("PLATFORM_ADMIN_TOKEN_TTL_MINUTES", "480")),
        cors_origins=os.environ.get("CORS_ORIGINS", "*"),
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )
