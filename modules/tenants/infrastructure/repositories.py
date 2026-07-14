from __future__ import annotations

from sqlalchemy import select

from core.infrastructure.base_repository import BaseRepository
from modules.tenants.infrastructure.models import BranchModel, TenantModel


class TenantRepository(BaseRepository[TenantModel]):
    model = TenantModel

    async def get_by_slug(self, slug: str) -> TenantModel | None:
        # Not tenant-scoped by definition (used to *resolve* the tenant), so
        # we bypass _base_query's tenant filter deliberately here.
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.slug == slug, TenantModel.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


class BranchRepository(BaseRepository[BranchModel]):
    model = BranchModel
