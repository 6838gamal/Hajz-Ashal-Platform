"""Seeds the fixed permissions catalog. Idempotent - safe to re-run.
Run with: python scripts/seed_permissions.py
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from modules.access_control.infrastructure.models import PermissionModel

CATALOG: list[tuple[str, str, str]] = [
    ("tenants.branches.create", "tenants", "Create a branch under the current tenant"),
    ("tenants.branches.read", "tenants", "View branches"),
    ("identity.users.manage", "identity", "Manage users within the current tenant"),
    ("access_control.roles.manage", "access_control", "Manage roles and permission assignments"),
    ("appointments.create", "appointments", "Book appointments"),
    ("appointments.read", "appointments", "View appointments"),
    ("appointments.cancel", "appointments", "Cancel appointments"),
    ("patients.manage", "patients", "Manage patient records"),
    ("doctors.manage", "doctors", "Manage doctor records"),
    ("dashboard.view", "dashboard", "View dashboard KPIs"),
    ("reporting.view", "reporting", "View and export reports"),
    ("subscriptions.manage", "subscriptions", "Manage the tenant's subscription and billing"),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing_codes = set((await session.execute(select(PermissionModel.code))).scalars().all())
        created = 0
        for code, module, description in CATALOG:
            if code in existing_codes:
                continue
            session.add(PermissionModel(code=code, module=module, description=description))
            created += 1
        await session.commit()
        print(f"Seeded {created} new permission(s); {len(existing_codes)} already existed.")


if __name__ == "__main__":
    asyncio.run(seed())
