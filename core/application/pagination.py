from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PageRequest:
    page: int = 1
    page_size: int = 20

    def __post_init__(self):
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if not (1 <= self.page_size <= 200):
            raise ValueError("page_size must be between 1 and 200")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class PageResult(Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    page_size: int
