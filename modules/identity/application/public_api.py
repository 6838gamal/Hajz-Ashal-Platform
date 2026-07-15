"""Public surface for other modules - currently only `platform_admin`,
managing users across every tenant. Like `tenants.application.public_api`,
these helpers query without any TenantContext filter (an optional explicit
`tenant_id` is used instead), since the platform-superadmin panel isn't
scoped to one tenant."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.security import hash_password
from modules.identity.infrastructure.models import UserModel
from modules.tenants.application.public_api import tenant_exists


async def list_users(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> tuple[list[UserModel], int]:
    query = select(UserModel).where(UserModel.deleted_at.is_(None))
    if tenant_id is not None:
        query = query.where(UserModel.tenant_id == tenant_id)
    if search:
        like = f"%{search}%"
        query = query.where(or_(UserModel.email.ilike(like), UserModel.full_name.ilike(like)))

    total = (await session.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    query = query.order_by(UserModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(query)).scalars().all()
    return list(rows), total


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> UserModel | None:
    return await session.get(UserModel, user_id)


async def create_user_admin(
    session: AsyncSession, *, tenant_id: uuid.UUID, email: str, password: str, full_name: str
) -> tuple[UserModel | None, str | None]:
    if not await tenant_exists(session, tenant_id):
        return None, "TENANT_NOT_FOUND"

    existing = (
        await session.execute(
            select(UserModel).where(
                UserModel.tenant_id == tenant_id, UserModel.email == email, UserModel.deleted_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return None, "EMAIL_TAKEN"

    user = UserModel(
        tenant_id=tenant_id,
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        status="active",
        created_at=datetime.now(timezone.utc),
    )
    session.add(user)
    await session.flush()
    return user, None


async def update_user_admin(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    full_name: str | None = None,
    status: str | None = None,
    password: str | None = None,
) -> UserModel | None:
    user = await session.get(UserModel, user_id)
    if user is None or user.deleted_at is not None:
        return None
    if full_name is not None:
        user.full_name = full_name
    if status is not None:
        user.status = status
    if password is not None:
        user.hashed_password = hash_password(password)
    user.updated_at = datetime.now(timezone.utc)
    await session.flush()
    return user


async def delete_user_admin(session: AsyncSession, user_id: uuid.UUID) -> bool:
    user = await session.get(UserModel, user_id)
    if user is None or user.deleted_at is not None:
        return False
    user.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return True
