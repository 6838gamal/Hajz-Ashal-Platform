"""The only surface other Modules are allowed to depend on. Nothing outside
`modules/access_control` should import from its infrastructure/domain
directly - see docs/architecture/01-analysis-and-domains.md section 1.5."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.access_control.infrastructure.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)


async def get_roles_and_permissions_for_user(
    session: AsyncSession, user_id: uuid.UUID
) -> tuple[list[str], list[str]]:
    """Used by `identity` at login time to embed roles/permissions in the JWT."""
    role_rows = (
        await session.execute(select(RoleModel.name).join(UserRoleModel, UserRoleModel.role_id == RoleModel.id).where(UserRoleModel.user_id == user_id))
    ).scalars().all()

    permission_rows = (
        await session.execute(
            select(PermissionModel.code)
            .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
            .join(UserRoleModel, UserRoleModel.role_id == RolePermissionModel.role_id)
            .where(UserRoleModel.user_id == user_id)
        )
    ).scalars().all()

    return list(dict.fromkeys(role_rows)), list(dict.fromkeys(permission_rows))


# ---------------------------------------------------------------------------
# Platform-admin surface: full RBAC CRUD across every tenant. Used only by
# `modules.platform_admin` - regular tenant-scoped modules should keep using
# `get_roles_and_permissions_for_user` above.
# ---------------------------------------------------------------------------


async def list_permissions(session: AsyncSession) -> list[PermissionModel]:
    rows = (
        await session.execute(select(PermissionModel).order_by(PermissionModel.module, PermissionModel.code))
    ).scalars().all()
    return list(rows)


async def list_roles(session: AsyncSession, *, tenant_id: uuid.UUID | None = None) -> list[RoleModel]:
    query = select(RoleModel).where(RoleModel.deleted_at.is_(None))
    if tenant_id is None:
        query = query.where(RoleModel.tenant_id.is_(None))
    else:
        query = query.where(or_(RoleModel.tenant_id == tenant_id, RoleModel.tenant_id.is_(None)))
    rows = (await session.execute(query.order_by(RoleModel.name))).scalars().all()
    return list(rows)


async def get_role(session: AsyncSession, role_id: uuid.UUID) -> RoleModel | None:
    return await session.get(RoleModel, role_id)


async def get_role_permission_codes(session: AsyncSession, role_id: uuid.UUID) -> list[str]:
    rows = (
        await session.execute(
            select(PermissionModel.code)
            .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
            .where(RolePermissionModel.role_id == role_id)
        )
    ).scalars().all()
    return list(rows)


async def _set_role_permissions(session: AsyncSession, role_id: uuid.UUID, permission_codes: list[str]) -> None:
    await session.execute(delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id))
    if permission_codes:
        permission_ids = (
            await session.execute(select(PermissionModel.id).where(PermissionModel.code.in_(permission_codes)))
        ).scalars().all()
        for permission_id in permission_ids:
            session.add(RolePermissionModel(role_id=role_id, permission_id=permission_id))
    await session.flush()


async def create_role(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    name: str,
    is_system_role: bool = False,
    permission_codes: list[str] | None = None,
) -> RoleModel:
    role = RoleModel(tenant_id=tenant_id, name=name, is_system_role=is_system_role, created_at=datetime.now(timezone.utc))
    session.add(role)
    await session.flush()
    if permission_codes:
        await _set_role_permissions(session, role.id, permission_codes)
    return role


async def update_role(
    session: AsyncSession,
    role_id: uuid.UUID,
    *,
    name: str | None = None,
    permission_codes: list[str] | None = None,
) -> RoleModel | None:
    role = await session.get(RoleModel, role_id)
    if role is None or role.deleted_at is not None:
        return None
    if name is not None:
        role.name = name
    role.updated_at = datetime.now(timezone.utc)
    if permission_codes is not None:
        await _set_role_permissions(session, role_id, permission_codes)
    await session.flush()
    return role


async def delete_role(session: AsyncSession, role_id: uuid.UUID) -> bool:
    role = await session.get(RoleModel, role_id)
    if role is None or role.deleted_at is not None:
        return False
    role.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return True


async def list_user_role_assignments(session: AsyncSession, user_id: uuid.UUID) -> list[tuple[UserRoleModel, str]]:
    rows = (
        await session.execute(
            select(UserRoleModel, RoleModel.name)
            .join(RoleModel, RoleModel.id == UserRoleModel.role_id)
            .where(UserRoleModel.user_id == user_id)
        )
    ).all()
    return [(assignment, name) for assignment, name in rows]


async def assign_role_to_user(
    session: AsyncSession, *, user_id: uuid.UUID, role_id: uuid.UUID, branch_id: uuid.UUID | None = None
) -> UserRoleModel:
    existing = (
        await session.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role_id,
                UserRoleModel.branch_id == branch_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    assignment = UserRoleModel(user_id=user_id, role_id=role_id, branch_id=branch_id)
    session.add(assignment)
    await session.flush()
    return assignment


async def remove_role_from_user(
    session: AsyncSession, *, user_id: uuid.UUID, role_id: uuid.UUID, branch_id: uuid.UUID | None = None
) -> bool:
    result = await session.execute(
        delete(UserRoleModel).where(
            UserRoleModel.user_id == user_id,
            UserRoleModel.role_id == role_id,
            UserRoleModel.branch_id == branch_id,
        )
    )
    await session.flush()
    return result.rowcount > 0
