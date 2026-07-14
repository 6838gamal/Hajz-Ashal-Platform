from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserRequest:
    tenant_id: uuid.UUID
    email: str
    password: str
    full_name: str


@dataclass(frozen=True)
class UserResponse:
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    status: str


@dataclass(frozen=True)
class LoginRequest:
    tenant_id: uuid.UUID
    email: str
    password: str


@dataclass(frozen=True)
class TokenPairResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class RefreshTokenRequest:
    refresh_token: str
