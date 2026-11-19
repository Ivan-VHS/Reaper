"""Typed, in-process routing primitives (no transport or serialization layer)."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any


class RelayError(RuntimeError):
    """Base class for relay registration and delivery failures."""


class UnknownRelayError(RelayError):
    """Raised when a destination is not registered."""


@dataclass(frozen=True, slots=True)
class RelayEndpoint:
    address: str
    payload_type: type[Any] | tuple[type[Any], ...]
    handler: Callable[[Any], Any]


class RelayBus:
    """A deterministic local dispatch table; remote delivery is deliberately absent."""

    def __init__(self, *, max_endpoints: int = 4096) -> None:
        if isinstance(max_endpoints, bool) or not isinstance(max_endpoints, int) or max_endpoints < 1:
            raise ValueError("max_endpoints must be a positive integer")
        self.max_endpoints = max_endpoints
        self._endpoints: dict[str, RelayEndpoint] = {}

    @property
    def endpoints(self) -> tuple[str, ...]:
        return tuple(sorted(self._endpoints))

    def register(
        self,
        address: str,
        handler: Callable[[Any], Any],
        *,
        payload_type: type[Any] | tuple[type[Any], ...] = object,
    ) -> None:
        if not isinstance(address, str) or not address.strip():
            raise ValueError("relay address must be a non-empty string")
        if not callable(handler):
            raise TypeError("relay handler must be callable")
        if not isinstance(payload_type, (type, tuple)):
            raise TypeError("payload_type must be a type or tuple of types")
        if address in self._endpoints:
            raise RelayError(f"relay '{address}' is already registered")
        if len(self._endpoints) >= self.max_endpoints:
            raise RelayError(f"relay endpoint limit ({self.max_endpoints}) exceeded")
        self._endpoints[address] = RelayEndpoint(address, payload_type, handler)

    def unregister(self, address: str) -> None:
        if address not in self._endpoints:
            raise UnknownRelayError(f"unknown relay '{address}'")
        del self._endpoints[address]

    def send(self, address: str, payload: Any) -> Any:
        try:
            endpoint = self._endpoints[address]
        except KeyError as error:
            raise UnknownRelayError(f"unknown relay '{address}'") from error
        if not isinstance(payload, endpoint.payload_type):
            expected = getattr(endpoint.payload_type, "__name__", repr(endpoint.payload_type))
            raise TypeError(f"relay '{address}' expects {expected}, got {type(payload).__name__}")
        return endpoint.handler(payload)
