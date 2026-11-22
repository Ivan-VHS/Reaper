"""OCTA-8 portable typed values for the Reaper reference runtime."""
from __future__ import annotations

import base64
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any, Callable

SCHEMA = "ivan-vhs.octa8.v1"
KINDS = ("null", "boolean", "integer", "number", "text", "bytes", "sequence", "record")
INT64_MIN, INT64_MAX = -(2 ** 63), (2 ** 63) - 1
MAX_DEPTH, MAX_ITEMS, MAX_TEXT, MAX_BYTES = 64, 100_000, 1_000_000, 16 * 1024 * 1024


class Octa8Error(ValueError):
    """Invalid OCTA-8 value or wire envelope."""


def octa8_kind(value: Any) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        if not INT64_MIN <= value <= INT64_MAX:
            raise Octa8Error("integer is outside the signed 64-bit OCTA-8 range")
        return "integer"
    if type(value) is float:
        if not math.isfinite(value):
            raise Octa8Error("OCTA-8 numbers must be finite")
        return "number"
    if isinstance(value, str):
        if len(value) > MAX_TEXT:
            raise Octa8Error("text exceeds the OCTA-8 length limit")
        return "text"
    if isinstance(value, (bytes, bytearray, memoryview)):
        if len(value) > MAX_BYTES:
            raise Octa8Error("byte sequence exceeds the OCTA-8 size limit")
        return "bytes"
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_ITEMS:
            raise Octa8Error("sequence exceeds the OCTA-8 item limit")
        return "sequence"
    if isinstance(value, Mapping):
        if len(value) > MAX_ITEMS or any(not isinstance(key, str) for key in value):
            raise Octa8Error("OCTA-8 records need bounded text keys")
        return "record"
    raise Octa8Error(f"unsupported OCTA-8 value type: {type(value).__name__}")


def _encode(value: Any, depth: int, budget: list[int]) -> dict[str, Any]:
    if depth > MAX_DEPTH:
        raise Octa8Error("OCTA-8 nesting depth limit exceeded")
    kind = octa8_kind(value)
    budget[0] += 1
    if budget[0] > MAX_ITEMS:
        raise Octa8Error("OCTA-8 total item limit exceeded")
    if kind == "bytes":
        encoded: Any = base64.b64encode(bytes(value)).decode("ascii")
    elif kind == "sequence":
        encoded = [_encode(item, depth + 1, budget) for item in value]
    elif kind == "record":
        encoded = {key: _encode(value[key], depth + 1, budget) for key in sorted(value)}
    else:
        encoded = value
    return {"kind": kind, "value": encoded}


def octa8_pack(value: Any) -> dict[str, Any]:
    """Encode a native value into the deterministic JSON wire envelope."""
    return {"schema": SCHEMA, **_encode(value, 0, [0])}


def _decode(node: Any, depth: int, budget: list[int]) -> Any:
    if depth > MAX_DEPTH or not isinstance(node, dict) or set(node) != {"kind", "value"}:
        raise Octa8Error("invalid OCTA-8 node or nesting depth")
    kind, value = node["kind"], node["value"]
    if kind not in KINDS:
        raise Octa8Error(f"unknown OCTA-8 kind: {kind!r}")
    budget[0] += 1
    if budget[0] > MAX_ITEMS:
        raise Octa8Error("OCTA-8 total item limit exceeded")
    if kind == "null":
        if value is not None:
            raise Octa8Error("null kind must carry null")
        return None
    if kind == "boolean":
        if type(value) is not bool:
            raise Octa8Error("boolean kind must carry boolean")
        return value
    if kind == "integer":
        if type(value) is not int or not INT64_MIN <= value <= INT64_MAX:
            raise Octa8Error("integer kind must carry signed 64-bit integer")
        return value
    if kind == "number":
        if type(value) not in (int, float) or not math.isfinite(value):
            raise Octa8Error("number kind must carry a finite number")
        return float(value)
    if kind == "text":
        if not isinstance(value, str) or len(value) > MAX_TEXT:
            raise Octa8Error("text kind must carry bounded text")
        return value
    if kind == "bytes":
        if not isinstance(value, str) or len(value) > ((MAX_BYTES + 2) // 3) * 4:
            raise Octa8Error("bytes kind must carry bounded base64 text")
        try:
            decoded = base64.b64decode(value.encode("ascii"), validate=True)
        except (UnicodeEncodeError, ValueError) as exc:
            raise Octa8Error("bytes kind contains invalid base64") from exc
        if len(decoded) > MAX_BYTES or base64.b64encode(decoded).decode("ascii") != value:
            raise Octa8Error("bytes kind contains non-canonical base64")
        return decoded
    if kind == "sequence":
        if not isinstance(value, list) or len(value) > MAX_ITEMS:
            raise Octa8Error("sequence kind must carry a bounded array")
        return [_decode(item, depth + 1, budget) for item in value]
    if not isinstance(value, dict) or len(value) > MAX_ITEMS:
        raise Octa8Error("record kind must carry a bounded object")
    return {key: _decode(value[key], depth + 1, budget) for key in sorted(value)}


def octa8_unpack(envelope: Any) -> Any:
    """Validate and decode a portable OCTA-8 envelope."""
    if not isinstance(envelope, dict) or set(envelope) != {"schema", "kind", "value"}:
        raise Octa8Error("invalid OCTA-8 envelope shape")
    if envelope.get("schema") != SCHEMA:
        raise Octa8Error("unsupported OCTA-8 schema")
    return _decode({"kind": envelope["kind"], "value": envelope["value"]}, 0, [0])


def octa8_validate(envelope: Any) -> bool:
    try:
        octa8_unpack(envelope)
        return True
    except (Octa8Error, TypeError, ValueError, OverflowError):
        return False


def octa8_digest(envelope: Any) -> str:
    """SHA-256 of the canonical, validated JSON representation."""
    octa8_unpack(envelope)
    data = json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def octa8_assert_kind(envelope: Any, expected: Any) -> bool:
    octa8_unpack(envelope)
    if not isinstance(expected, str) or expected not in KINDS:
        raise Octa8Error("expected kind must be one of: " + ", ".join(KINDS))
    if envelope["kind"] != expected:
        raise Octa8Error(f"expected OCTA-8 {expected}, got {envelope['kind']}")
    return True


def octa8_map(envelope: Any, transform: Callable[[Any], Any]) -> dict[str, Any]:
    if not callable(transform):
        raise Octa8Error("OCTA-8 map requires a callable transformation")
    return octa8_pack(transform(octa8_unpack(envelope)))


def octa8_schema_id() -> str:
    return SCHEMA
