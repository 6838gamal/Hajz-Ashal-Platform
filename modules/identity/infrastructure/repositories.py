from __future__ import annotations

import uuid

from sqlalchemy import select

from core.infrastructure.base_repository import BaseRepository
from modules.identity.infrastructure.models import RefreshTokenModel, UserModel


class UserRepository(BaseRepository[UserModel]):
    model = UserModel

    async def get_by_email(self, tenant_id: uuid.UUID, email: str) -> UserModel | None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.tenant_id == tenant_id,
                UserModel.email == email,
                UserModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


class RefreshTokenRepository:
    def __init__(self, session):
        self._session = session

    async def add(self, token: RefreshTokenModel) -> RefreshTokenModel:
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_id(self, token_id: uuid.UUID) -> RefreshTokenModel | None:
        return await self._session.get(RefreshTokenModel, token_id)

    async def revoke(self, token: RefreshTokenModel) -> None:
        from datetime import datetime, timezone

        token.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()
