"""Async SQLAlchemy engine/session shared by every module. Each module owns
its own ORM models (infrastructure/persistence/models.py) but they all
declare against this one shared Base/metadata + engine, since this is a
single Modular Monolith database, not per-module databases."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.async_database_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
