"""Public surface for other modules (e.g. `identity` resolving a tenant by
slug during registration)."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.tenants.infrastructure.repositories import TenantRepository


async def tenant_exists(session: AsyncSession, tenant_id) -> bool:
    repo = TenantRepository(session)
    from core.infrastructure.tenant_context import TenantContext

    # This lookup happens before a tenant context is established (e.g. during
    # registration), so query directly rather than through the tenant-scoped
    # base query.
    model = await session.get(TenantRepository.model, tenant_id)
    return model is not None and model.deleted_at is None
