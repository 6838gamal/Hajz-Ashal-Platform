"""The only surface other Modules are allowed to depend on. Nothing outside
`modules/access_control` should import from its infrastructure/domain
directly - see docs/architecture/01-analysis-and-domains.md section 1.5."""
from __future__ import annotations

import uuid

from sqlalchemy import select
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
