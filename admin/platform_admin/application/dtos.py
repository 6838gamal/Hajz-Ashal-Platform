from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformLoginRequest:
    email: str
    password: str


@dataclass(frozen=True)
class PlatformTokenResponse:
    access_token: str
    full_name: str
    email: str
