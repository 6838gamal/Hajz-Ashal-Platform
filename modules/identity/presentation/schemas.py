from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterUserSchema(BaseModel):
    tenant_id: uuid.UUID
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)


class UserSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    status: str


class LoginSchema(BaseModel):
    tenant_id: uuid.UUID
    email: EmailStr
    password: str


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    refresh_token: str
