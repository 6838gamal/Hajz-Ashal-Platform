"""Minimal DI container: a dict-based service locator + factory functions,
as decided in docs/architecture/03-layers-and-api-design.md section 3.6.
No external DI library - kept deliberately simple since FastAPI's own
Depends() already does the per-request wiring; this container only holds
module-level singletons/factories that Depends() call sites resolve from."""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class Container:
    def __init__(self) -> None:
        self._factories: dict[type, Callable[..., object]] = {}

    def register(self, interface: type[T], factory: Callable[..., T]) -> None:
        self._factories[interface] = factory

    def resolve(self, interface: type[T], *args, **kwargs) -> T:
        if interface not in self._factories:
            raise LookupError(f"No provider registered for {interface!r}")
        return self._factories[interface](*args, **kwargs)  # type: ignore[return-value]


container = Container()
