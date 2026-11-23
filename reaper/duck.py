"""Duck-profile helpers for safe structural inspection in Reaper.

The profile deliberately operates on Reaper maps and known runtime value kinds.
It does not inspect arbitrary Python attributes or execute user-supplied methods.
"""
from __future__ import annotations

from typing import Any


_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "nothing": ("empty",),
    "boolean": ("boolean",),
    "number": ("numeric",),
    "text": ("indexable", "iterable", "sized", "text"),
    "list": ("indexable", "iterable", "sized"),
    "range": ("indexable", "iterable", "sized"),
    "map": ("indexable", "iterable", "keyed", "sized", "structural"),
    "craft": ("callable",),
    "resource": ("resource",),
}


def capabilities(kind: str) -> list[str]:
    """Return the stable capability names for a known Reaper value kind."""
    return list(_CAPABILITIES.get(kind, ()))


def supports(kind: str, capability: str) -> bool:
    """Check a named capability without probing host-language attributes."""
    if not isinstance(capability, str):
        raise TypeError("duck_supports capability must be text")
    return capability in _CAPABILITIES.get(kind, ())


def has(value: Any, field: str) -> bool:
    """Test whether a Reaper map contains a field, including fields set to nothing."""
    if not isinstance(value, dict):
        raise TypeError("duck_has expects a map as its first argument")
    if not isinstance(field, str):
        raise TypeError("duck_has field name must be text")
    return field in value


def _required_fields(required: Any, limit: int) -> list[str]:
    if isinstance(required, str):
        fields = [required]
    elif isinstance(required, list):
        fields = required
    else:
        raise TypeError("required fields must be text or a list of text")

    if len(fields) > limit:
        raise ValueError(f"duck contract field limit ({limit}) exceeded")
    if any(not isinstance(field, str) for field in fields):
        raise TypeError("every required field name must be text")

    # Preserve declaration order while removing duplicate checks.
    return list(dict.fromkeys(fields))


def probe(value: Any, required: Any, kind: str, limit: int) -> dict[str, Any]:
    """Return a quiet, deterministic preflight report for a structural map contract."""
    fields = _required_fields(required, limit)
    if not isinstance(value, dict):
        return {"ok": False, "kind": kind, "missing": fields}

    if len(value) > limit:
        raise ValueError(f"duck map item limit ({limit}) exceeded")
    missing = [field for field in fields if field not in value]
    return {"ok": not missing, "kind": kind, "missing": missing}


def require(value: Any, required: Any, limit: int) -> Any:
    """Enforce a structural map contract and return the original map unchanged."""
    if not isinstance(value, dict):
        raise TypeError("duck_require expects a map as its first argument")

    report = probe(value, required, "map", limit)
    if not report["ok"]:
        missing = ", ".join(report["missing"])
        raise ValueError(f"duck contract is missing required field(s): {missing}")
    return value


def adapt(value: Any, defaults: Any, limit: int) -> dict[str, Any]:
    """Return a new map with missing defaults added; never overwrite caller values."""
    if not isinstance(value, dict) or not isinstance(defaults, dict):
        raise TypeError("duck_adapt expects two maps")

    if len(value) > limit or len(defaults) > limit:
        raise ValueError(f"duck map item limit ({limit}) exceeded")
    if any(not isinstance(key, str) for key in value):
        raise TypeError("duck_adapt source map keys must be text")
    if any(not isinstance(key, str) for key in defaults):
        raise TypeError("duck_adapt defaults map keys must be text")

    result = dict(value)
    for key, default in defaults.items():
        if key not in result:
            result[key] = default
            if len(result) > limit:
                raise ValueError(f"duck map item limit ({limit}) exceeded")
    return result


def inspect(value: Any, kind: str, item_limit: int, text_limit: int) -> dict[str, Any]:
    """Describe a value without exposing its contents or host object internals."""
    summary: dict[str, Any] = {
        "kind": kind,
        "capabilities": capabilities(kind),
    }

    if isinstance(value, dict):
        if len(value) > item_limit:
            raise ValueError(f"duck map item limit ({item_limit}) exceeded")
        summary["size"] = len(value)
        if all(isinstance(key, str) for key in value):
            summary["fields"] = sorted(value)
    elif isinstance(value, (list, tuple, range)):
        size = len(value)
        if size > item_limit:
            raise ValueError(f"duck collection item limit ({item_limit}) exceeded")
        summary["size"] = size
    elif isinstance(value, str):
        if len(value) > text_limit:
            raise ValueError(f"duck text limit ({text_limit}) exceeded")
        summary["size"] = len(value)

    return summary
