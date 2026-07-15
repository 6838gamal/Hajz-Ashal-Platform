"""Creates (or resets) a platform super-admin account - the one identity that
manages every tenant from /admin. Idempotent by email; safe to re-run.

Run with:
    python scripts/create_platform_admin.py --email you@example.com --name "Owner"
    python scripts/create_platform_admin.py --email you@example.com --name "Owner" --password "..."

If --password is omitted, a secure random password is generated and printed
once - store it immediately, it is not saved anywhere in plaintext.
"""
from __future__ import annotations

import argparse
import asyncio
import secrets
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from core.infrastructure.security import hash_password
from modules.platform_admin.infrastructure.models import PlatformAdminModel


async def _create_or_update(email: str, password: str | None, full_name: str) -> str:
    if password is None:
        password = secrets.token_urlsafe(12)

    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(PlatformAdminModel).where(PlatformAdminModel.email == email))
        ).scalar_one_or_none()

        if existing is not None:
            existing.hashed_password = hash_password(password)
            existing.full_name = full_name
            existing.status = "active"
            existing.deleted_at = None
            existing.updated_at = datetime.now(timezone.utc)
        else:
            session.add(
                PlatformAdminModel(
                    email=email,
                    hashed_password=hash_password(password),
                    full_name=full_name,
                    status="active",
                    created_at=datetime.now(timezone.utc),
                )
            )
        await session.commit()

    return password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", default=None, help="Omit to auto-generate a secure password.")
    parser.add_argument("--name", default="مالك المنصة")
    args = parser.parse_args()

    password_was_generated = args.password is None
    password = asyncio.run(_create_or_update(args.email, args.password, args.name))

    if password_was_generated:
        print(f"Platform admin '{args.email}' is ready. Generated password: {password}")
        print("Log in at /admin/login and change it as soon as possible.")
    else:
        print(f"Platform admin '{args.email}' is ready.")


if __name__ == "__main__":
    main()
