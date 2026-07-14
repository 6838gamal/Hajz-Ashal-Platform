"""Result Pattern: use cases return Result[T] instead of raising exceptions
for expected business failures (validation, conflicts, not-found). Real
exceptions are reserved for truly unexpected errors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Error:
    code: str
    message: str
    details: dict | None = None


@dataclass(frozen=True)
class Result(Generic[T]):
    _value: T | None
    _error: Error | None
    is_success: bool

    @staticmethod
    def success(value: T) -> "Result[T]":
        return Result(_value=value, _error=None, is_success=True)

    @staticmethod
    def failure(error: Error) -> "Result[T]":
        return Result(_value=None, _error=error, is_success=False)

    @property
    def value(self) -> T:
        if not self.is_success:
            raise ValueError(f"Cannot access .value on a failed Result: {self._error}")
        return self._value  # type: ignore[return-value]

    @property
    def error(self) -> Error:
        if self.is_success:
            raise ValueError("Cannot access .error on a successful Result")
        return self._error  # type: ignore[return-value]

    @property
    def is_failure(self) -> bool:
        return not self.is_success
