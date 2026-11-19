"""Typed in-process routing for Reaper's Citadel architecture layer.

The router avoids serialization inside one process, but it is not a network
transport and it does not make dispatch a zero-cost operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable


class RelayError(RuntimeError):
    """Base class for relay lookup and dispatch failures."""


class RelayNotFoundError(RelayError):
    """Raised when a destination has not been registered."""


class RelayPayloadError(RelayError):
    """Raised when a route receives a payload of the wrong type."""


@dataclass(frozen=True, slots=True)
class RelayStats:
    destination: str
    dispatches: int
    failures: int
    rejected: int


@dataclass(frozen=True, slots=True)
class _Route:
    handler: Callable[[Any], Any]
    payload_type: type[Any] | tuple[type[Any], ...] | None


class CitadelRouter:
    """Thread-safe named routes with optional runtime payload validation.

    Route lookup and counters are protected by a lock. User handlers execute
    outside the lock so a slow callback cannot block route registration or
    dispatch to unrelated destinations.
    """

    def __init__(self, max_routes: int = 1_024) -> None:
        if max_routes < 1:
            raise ValueError("max_routes must be positive")
        self.max_routes = max_routes
        self._routes: dict[str, _Route] = {}
        self._counters: dict[str, list[int]] = {}
        self._lock = RLock()

    @staticmethod
    def _validate_payload_type(
        payload_type: type[Any] | tuple[type[Any], ...] | None,
    ) -> None:
        if payload_type is None:
            return
        candidates = payload_type if isinstance(payload_type, tuple) else (payload_type,)
        if not candidates or any(not isinstance(item, type) for item in candidates):
            raise TypeError("payload_type must be a type, a non-empty tuple of types, or None")

    def register(
        self,
        destination: str,
        handler: Callable[[Any], Any],
        *,
        payload_type: type[Any] | tuple[type[Any], ...] | None = None,
    ) -> None:
        if not isinstance(destination, str) or not destination.strip():
            raise ValueError("destination must be a non-empty string")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._validate_payload_type(payload_type)
        with self._lock:
            if destination in self._routes:
                raise RelayError(f"destination '{destination}' is already registered")
            if len(self._routes) >= self.max_routes:
                raise RelayError(f"route limit ({self.max_routes}) exceeded")
            self._routes[destination] = _Route(handler, payload_type)
            self._counters[destination] = [0, 0, 0]

    def unregister(self, destination: str) -> bool:
        with self._lock:
            removed = self._routes.pop(destination, None) is not None
            if removed:
                self._counters.pop(destination, None)
            return removed

    def dispatch(self, destination: str, payload: Any) -> Any:
        with self._lock:
            route = self._routes.get(destination)
            if route is None:
                raise RelayNotFoundError(f"unknown relay destination '{destination}'")
            counters = self._counters[destination]
            if route.payload_type is not None and not isinstance(payload, route.payload_type):
                counters[2] += 1
                expected = getattr(route.payload_type, "__name__", repr(route.payload_type))
                raise RelayPayloadError(
                    f"relay '{destination}' expects {expected}, got {type(payload).__name__}"
                )
            counters[0] += 1

        try:
            return route.handler(payload)
        except Exception:
            with self._lock:
                current = self._counters.get(destination)
                if current is not None:
                    current[1] += 1
            raise

    def destinations(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._routes))

    def stats(self) -> tuple[RelayStats, ...]:
        with self._lock:
            return tuple(
                RelayStats(name, counts[0], counts[1], counts[2])
                for name, counts in sorted(self._counters.items())
            )
