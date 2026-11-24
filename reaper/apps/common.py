"""Shared validation helpers for the first-party Reaper application suite."""
from __future__ import annotations

import math
from typing import Any


class ApplicationInputError(ValueError):
    """The supplied application payload violates its versioned input contract."""


def require_object(value: Any, label: str = "payload") -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ApplicationInputError(f"{label} must be a JSON object with text keys")
    return value


def require_array(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ApplicationInputError(f"'{key}' must be an array")
    return value


def require_text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ApplicationInputError(f"{label} must be text")
    if not allow_empty and not value.strip():
        raise ApplicationInputError(f"{label} must not be empty")
    return value


def require_number(value: Any, label: str, *, minimum: float | None = None,
                   maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ApplicationInputError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ApplicationInputError(f"{label} must be finite")
    if minimum is not None and result < minimum:
        raise ApplicationInputError(f"{label} must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ApplicationInputError(f"{label} must be <= {maximum}")
    return result


def require_integer(value: Any, label: str, *, minimum: int | None = None,
                    maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ApplicationInputError(f"{label} must be a whole number")
    if minimum is not None and value < minimum:
        raise ApplicationInputError(f"{label} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ApplicationInputError(f"{label} must be <= {maximum}")
    return value


def optional_number(payload: dict[str, Any], key: str, default: float,
                    *, minimum: float | None = None, maximum: float | None = None) -> float:
    if key not in payload:
        return default
    return require_number(payload[key], key, minimum=minimum, maximum=maximum)


def optional_text(payload: dict[str, Any], key: str, default: str = "") -> str:
    if key not in payload:
        return default
    return require_text(payload[key], key, allow_empty=True)
