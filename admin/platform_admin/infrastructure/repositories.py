from __future__ import annotations

from sqlalchemy import select

from core.infrastructure.base_repository import BaseRepository
from admin.platform_admin.infrastructure.models import PlatformAdminModel


class PlatformAdminRepository(BaseRepository[PlatformAdminModel]):
    model = PlatformAdminModel

    async def get_by_email(self, email: str) -> PlatformAdminModel | None:
        result = await self._session.execute(
            select(PlatformAdminModel).where(
                PlatformAdminModel.email == email,
                PlatformAdminModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
