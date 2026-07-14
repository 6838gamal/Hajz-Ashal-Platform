"""Generic async Repository base. Every Module's Infrastructure repository
extends this instead of writing raw SQLAlchemy query boilerplate. Tenant
scoping is applied automatically for any model with a `tenant_id` column -
callers cannot accidentally bypass it."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.application.pagination import PageRequest, PageResult
from core.infrastructure.tenant_context import TenantContext

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, session: AsyncSession):
        self._session = session

    def _base_query(self, *, include_deleted: bool = False):
        query = select(self.model)
        if hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == TenantContext.require())
        if hasattr(self.model, "deleted_at") and not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        return query

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        query = self._base_query().where(self.model.id == entity_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def add(self, instance: ModelT) -> ModelT:
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def soft_delete(self, instance: ModelT, *, by: uuid.UUID | None = None) -> None:
        instance.deleted_at = datetime.now(timezone.utc)
        if hasattr(instance, "deleted_by"):
            instance.deleted_by = by
        await self._session.flush()

    async def list_page(self, page_request: PageRequest, *extra_filters) -> PageResult[ModelT]:
        query = self._base_query()
        for f in extra_filters:
            query = query.where(f)
        count_query = select(self.model).where(query.whereclause) if query.whereclause is not None else query
        total = len((await self._session.execute(count_query)).scalars().all())
        query = query.offset(page_request.offset).limit(page_request.page_size)
        rows = (await self._session.execute(query)).scalars().all()
        return PageResult(items=rows, total=total, page=page_request.page, page_size=page_request.page_size)
