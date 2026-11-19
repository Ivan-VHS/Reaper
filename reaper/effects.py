"""Task-local effect context propagation for host-side Reaper integrations."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from types import MappingProxyType
from collections.abc import Iterator, Mapping
from typing import Any


class EffectUnavailableError(LookupError):
    """Raised when code requests an effect absent from the active context."""


_EFFECTS: ContextVar[Mapping[str, Any]] = ContextVar("reaper_effects", default=MappingProxyType({}))


def current_effects() -> Mapping[str, Any]:
    """Return an immutable view of the current task-local effect bindings."""
    return _EFFECTS.get()


def get_effect(name: str) -> Any:
    if not isinstance(name, str) or not name:
        raise ValueError("effect name must be a non-empty string")
    try:
        return _EFFECTS.get()[name]
    except KeyError as error:
        raise EffectUnavailableError(f"effect '{name}' is not available in this context") from error


def require_effect(name: str, expected_type: type[Any] | tuple[type[Any], ...] | None = None) -> Any:
    value = get_effect(name)
    if expected_type is not None and not isinstance(value, expected_type):
        raise TypeError(f"effect '{name}' has an incompatible value type")
    return value


@contextmanager
def effect_scope(effects: Mapping[str, Any] | None = None, **bindings: Any) -> Iterator[Mapping[str, Any]]:
    """Temporarily extend the current context; nested scopes shadow outer names."""
    merged = dict(_EFFECTS.get())
    if effects is not None:
        if not isinstance(effects, Mapping):
            raise TypeError("effects must be a mapping")
        merged.update(effects)
    merged.update(bindings)
    if any(not isinstance(name, str) or not name for name in merged):
        raise ValueError("effect names must be non-empty strings")
    immutable = MappingProxyType(merged)
    token: Token[Mapping[str, Any]] = _EFFECTS.set(immutable)
    try:
        yield immutable
    finally:
        _EFFECTS.reset(token)
