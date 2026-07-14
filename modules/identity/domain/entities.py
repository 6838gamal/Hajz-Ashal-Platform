from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from core.domain.base_entity import TenantScopedEntity

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass(kw_only=True)
class User(TenantScopedEntity):
    email: str
    hashed_password: str
    full_name: str
    status: UserStatus = UserStatus.ACTIVE

    def __post_init__(self):
        if not _EMAIL_RE.match(self.email):
            raise ValueError("Invalid email address")
        if not self.full_name.strip():
            raise ValueError("full_name must not be empty")
