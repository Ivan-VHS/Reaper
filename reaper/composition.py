"""Bounded, deterministic concatenation and explicit function composition.

These are library primitives; they are not implicit language built-ins and do
not grant host I/O, network, subprocess, or filesystem effects.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

DEFAULT_MAX_ITEMS = 100_000
DEFAULT_MAX_TEXT_LENGTH = 1_000_000
DEFAULT_MAX_KEYS = 100_000


def _positive_limit(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def concat(*parts: Iterable[T], max_items: int = DEFAULT_MAX_ITEMS) -> tuple[T, ...]:
    """Concatenate iterable parts in their supplied order into an immutable tuple.

    The operation is eager and bounded. It never changes the input collections.
    """
    _positive_limit(max_items, "max_items")
    result: list[T] = []
    for part in parts:
        try:
            iterator = iter(part)
        except TypeError as error:
            raise TypeError("each concatenation part must be iterable") from error
        for item in iterator:
            if len(result) >= max_items:
                raise ValueError(f"concatenation exceeds max_items={max_items}")
            result.append(item)
    return tuple(result)


def concat_text(
    *parts: str,
    separator: str = "",
    max_length: int = DEFAULT_MAX_TEXT_LENGTH,
) -> str:
    """Join text fragments in order after validating the complete output size."""
    _positive_limit(max_length, "max_length")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")
    total = max(0, len(parts) - 1) * len(separator)
    for part in parts:
        if not isinstance(part, str):
            raise TypeError("all text fragments must be strings")
        total += len(part)
        if total > max_length:
            raise ValueError(f"text concatenation exceeds max_length={max_length}")
    if total > max_length:
        raise ValueError(f"text concatenation exceeds max_length={max_length}")
    return separator.join(parts)


def merge_mappings(
    *mappings: Mapping[Any, T],
    on_conflict: str = "error",
    max_keys: int = DEFAULT_MAX_KEYS,
) -> dict[Any, T]:
    """Merge mappings in order with an explicit key-conflict policy.

    on_conflict is one of: "error", "first", or "last". Insertion order follows
    first appearance of each key; "last" replaces only the associated value.
    """
    _positive_limit(max_keys, "max_keys")
    if on_conflict not in {"error", "first", "last"}:
        raise ValueError("on_conflict must be 'error', 'first', or 'last'")
    result: dict[Any, T] = {}
    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            raise TypeError("each mapping part must implement Mapping")
        for key, value in mapping.items():
            if key in result:
                if on_conflict == "error":
                    raise ValueError(f"mapping key conflict: {key!r}")
                if on_conflict == "first":
                    continue
                result[key] = value
                continue
            if len(result) >= max_keys:
                raise ValueError(f"mapping merge exceeds max_keys={max_keys}")
            result[key] = value
    return result


def compose(*functions: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Compose functions right-to-left: compose(f, g)(x) equals f(g(x))."""
    if any(not callable(function) for function in functions):
        raise TypeError("all composition members must be callable")

    def composed(value: Any) -> Any:
        for function in reversed(functions):
            value = function(value)
        return value

    return composed


def pipe(value: T, *functions: Callable[[Any], Any]) -> Any:
    """Apply functions left-to-right, matching Reaper's data-flow direction."""
    if any(not callable(function) for function in functions):
        raise TypeError("all pipeline members must be callable")
    for function in functions:
        value = function(value)
    return value
