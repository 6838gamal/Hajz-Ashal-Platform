"""Base Entity / Aggregate Root shared by every module's Domain layer.

Kept framework-agnostic on purpose: no SQLAlchemy, no Pydantic. ORM models and
DTOs are mapped to/from these in the Infrastructure and Presentation layers.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def new_id() -> uuid.UUID:
    return uuid.uuid4()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(kw_only=True)
class BaseEntity:
    """Common audit + identity fields required on every domain entity."""

    id: uuid.UUID = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    deleted_by: uuid.UUID | None = None
    version: int = 1

    def mark_updated(self, by: uuid.UUID | None = None) -> None:
        self.updated_at = utc_now()
        self.updated_by = by
        self.version += 1

    def mark_deleted(self, by: uuid.UUID | None = None) -> None:
        self.deleted_at = utc_now()
        self.deleted_by = by
        self.version += 1

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


@dataclass(kw_only=True)
class TenantScopedEntity(BaseEntity):
    """Base for every entity that belongs to a Tenant (almost everything)."""

    tenant_id: uuid.UUID


class AggregateRoot(BaseEntity):
    """Marker base class for Aggregate Roots that additionally collect
    Domain Events to be dispatched after a successful Unit of Work commit."""

    def __post_init__(self) -> None:
        self._domain_events: list[object] = []

    def register_event(self, event: object) -> None:
        if not hasattr(self, "_domain_events"):
            self._domain_events = []
        self._domain_events.append(event)

    def pull_events(self) -> list[object]:
        events = getattr(self, "_domain_events", [])
        self._domain_events = []
        return events
