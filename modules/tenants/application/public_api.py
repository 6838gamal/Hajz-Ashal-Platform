"""Public surface for other modules (e.g. `identity` resolving a tenant by
slug during registration, or `platform_admin` managing every tenant).

The listing/CRUD helpers below deliberately query without any TenantContext
filter - they are the cross-tenant surface used by the platform-superadmin
panel, which by definition isn't scoped to one tenant."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.tenants.infrastructure.models import BranchModel, TenantModel
from modules.tenants.infrastructure.repositories import TenantRepository


async def tenant_exists(session: AsyncSession, tenant_id) -> bool:
    # This lookup happens before a tenant context is established (e.g. during
    # registration), so query directly rather than through the tenant-scoped
    # base query.
    model = await session.get(TenantRepository.model, tenant_id)
    return model is not None and model.deleted_at is None


async def list_tenants(
    session: AsyncSession, *, page: int = 1, page_size: int = 20, search: str | None = None
) -> tuple[list[TenantModel], int]:
    query = select(TenantModel).where(TenantModel.deleted_at.is_(None))
    if search:
        like = f"%{search}%"
        query = query.where(or_(TenantModel.name.ilike(like), TenantModel.slug.ilike(like)))

    total = (await session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    query = query.order_by(TenantModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(query)).scalars().all()
    return list(rows), total


async def get_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> TenantModel | None:
    return await session.get(TenantModel, tenant_id)


async def update_tenant(
    session: AsyncSession, tenant_id: uuid.UUID, *, name: str | None = None, status: str | None = None
) -> TenantModel | None:
    tenant = await session.get(TenantModel, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        return None
    if name is not None:
        tenant.name = name
    if status is not None:
        tenant.status = status
    tenant.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return tenant


async def delete_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    tenant = await session.get(TenantModel, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        return False
    tenant.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return True


async def list_branches(session: AsyncSession, tenant_id: uuid.UUID) -> list[BranchModel]:
    rows = (
        await session.execute(
            select(BranchModel)
            .where(BranchModel.tenant_id == tenant_id, BranchModel.deleted_at.is_(None))
            .order_by(BranchModel.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def create_branch_for_tenant(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str,
    address: str | None = None,
    timezone_: str = "UTC",
) -> BranchModel | None:
    tenant = await session.get(TenantModel, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        return None
    branch = BranchModel(
        tenant_id=tenant_id, name=name, address=address, timezone=timezone_, created_at=datetime.now(timezone.utc)
    )
    session.add(branch)
    await session.flush()
    return branch


async def update_branch(
    session: AsyncSession,
    branch_id: uuid.UUID,
    *,
    name: str | None = None,
    address: str | None = None,
    timezone_: str | None = None,
) -> BranchModel | None:
    branch = await session.get(BranchModel, branch_id)
    if branch is None or branch.deleted_at is not None:
        return None
    if name is not None:
        branch.name = name
    if address is not None:
        branch.address = address
    if timezone_ is not None:
        branch.timezone = timezone_
    branch.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return branch


async def delete_branch(session: AsyncSession, branch_id: uuid.UUID) -> bool:
    branch = await session.get(BranchModel, branch_id)
    if branch is None or branch.deleted_at is not None:
        return False
    branch.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return True
