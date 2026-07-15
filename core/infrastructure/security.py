"""JWT issuing/verification and password hashing shared by every module
that needs authentication (currently just `identity`, but kept in Core
since it is cross-cutting infrastructure, not business logic)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    *,
    secret_key: str,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    roles: list[str],
    permissions: list[str],
    ttl_minutes: int,
    scope: str = "tenant",
) -> str:
    """`scope` distinguishes a normal tenant-user session ("tenant", the
    default - backward compatible with every existing caller) from a
    platform-superadmin session ("platform_admin", never tied to a tenant).
    Consumers must check `scope` explicitly before trusting cross-tenant
    claims - see modules/platform_admin/presentation/dependencies.py."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "roles": roles,
        "permissions": permissions,
        "scope": scope,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_token(token: str, *, secret_key: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
