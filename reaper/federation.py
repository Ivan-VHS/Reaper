"""Bounded JSON contracts for read-only OPlague federation."""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from . import metric_space
from .native import pytyliki_distance

OPLAGE_SNAPSHOT_SCHEMA = "oplage.device-snapshot.v1"
REAPER_COMPARISON_SCHEMA = "reaper.oplage-comparison.v1"
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_METRICS = 128
MAX_DEVICES = 10_000


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not permitted: {value}")


def read_json(path: str | os.PathLike[str]) -> Any:
    """Read bounded UTF-8 JSON; reject duplicate keys and NaN/Infinity."""
    source = Path(path)
    if source.is_symlink():
        raise ValueError("JSON input cannot be a symbolic link")
    if not source.is_file():
        raise ValueError(f"JSON input is not a regular file: {source}")
    size = source.stat().st_size
    if size > MAX_JSON_BYTES:
        raise ValueError(f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    raw = source.read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError(f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid UTF-8 JSON: {error}") from error


def write_json(path: str | os.PathLike[str], value: Any) -> str:
    """Atomically write finite JSON to an explicit file path."""
    destination = Path(path)
    parent = destination.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError(f"JSON output directory does not exist: {parent}")
    if destination.is_dir():
        raise ValueError(f"JSON output path is a directory: {destination}")
    try:
        encoded = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"value cannot be represented as finite JSON: {error}") from error
    if len(encoded) > MAX_JSON_BYTES:
        raise ValueError(f"JSON output exceeds {MAX_JSON_BYTES} bytes")

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(parent)
    )
    try:
        with os.fdopen(file_descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return str(destination)


_SNAPSHOT_REQUIRED_FIELDS = {
    "schema", "captured_utc", "source", "summary", "metrics",
    "devices", "packages", "snapshot_sha256",
}
_SNAPSHOT_SUMMARY_FIELDS = {
    "total_devices", "ok_devices", "problem_devices", "other_status_devices",
    "devices_with_class", "devices_with_identity", "audited_packages",
    "valid_packages",
}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def validate_oplage_snapshot(snapshot: Any) -> dict[str, float]:
    """Validate OPlague v1 structure, derived counters and canonical fingerprint."""
    label = "OPlague snapshot"
    if not isinstance(snapshot, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    if snapshot.get("schema") != OPLAGE_SNAPSHOT_SCHEMA:
        raise ValueError(f"{label} schema must be {OPLAGE_SNAPSHOT_SCHEMA}")
    keys = set(snapshot)
    allowed = _SNAPSHOT_REQUIRED_FIELDS | {"identity_protection"}
    missing = _SNAPSHOT_REQUIRED_FIELDS - keys
    extra = keys - allowed
    if missing or extra:
        raise ValueError(
            f"{label} fields are invalid; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    captured = snapshot.get("captured_utc")
    if not isinstance(captured, str):
        raise TypeError(f"{label}.captured_utc must be date-time text")
    try:
        captured_at = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label}.captured_utc must be an ISO 8601 date-time") from error
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError(f"{label}.captured_utc must include a timezone")

    source = snapshot.get("source")
    if not isinstance(source, Mapping) or set(source) != {"provider", "mode"}:
        raise ValueError(f"{label}.source must contain provider and mode only")
    if not isinstance(source.get("provider"), str) or source.get("mode") != "read_only":
        raise ValueError(f"{label}.source must declare a provider and read_only mode")

    identity = snapshot.get("identity_protection")
    if identity is not None:
        if not isinstance(identity, Mapping) or set(identity) != {"algorithm", "key_scope"}:
            raise ValueError(f"{label}.identity_protection has an invalid shape")
        if identity.get("algorithm") != "HMAC-SHA-256" or identity.get("key_scope") not in {
            "snapshot_ephemeral", "caller_managed"
        }:
            raise ValueError(f"{label}.identity_protection is unsupported")

    summary = snapshot.get("summary")
    if not isinstance(summary, Mapping) or set(summary) != _SNAPSHOT_SUMMARY_FIELDS:
        raise ValueError(f"{label}.summary must contain the eight v1 counters")
    for name, value in summary.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label}.summary.{name} must be a non-negative integer")

    metrics = snapshot.get("metrics")
    if not isinstance(metrics, Mapping) or not 6 <= len(metrics) <= MAX_METRICS:
        raise ValueError(f"{label}.metrics must contain 6..{MAX_METRICS} normalized metrics")
    normalized: dict[str, float] = {}
    for raw_name, raw_value in metrics.items():
        if not isinstance(raw_name, str) or not raw_name.strip() or len(raw_name) > 128:
            raise ValueError(f"{label}.metrics contains an invalid name")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise TypeError(f"{label}.metrics.{raw_name} must be a real number")
        try:
            value = float(raw_value)
        except OverflowError as error:
            raise ValueError(f"{label}.metrics.{raw_name} exceeds the float64 range") from error
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{label}.metrics.{raw_name} must be finite and within [0, 1]")
        normalized[raw_name] = value

    devices = snapshot.get("devices")
    if not isinstance(devices, list) or len(devices) > MAX_DEVICES:
        raise ValueError(f"{label}.devices must contain at most {MAX_DEVICES} records")
    for index, device in enumerate(devices):
        required = {
            "identity_sha256", "friendly_name", "class", "status",
            "problem_code", "problem_reported",
        }
        if not isinstance(device, Mapping) or set(device) != required:
            raise ValueError(f"{label}.devices[{index}] has an invalid shape")
        identity_value = device.get("identity_sha256")
        if not isinstance(identity_value, str) or (
            identity_value and _SHA256_PATTERN.fullmatch(identity_value) is None
        ):
            raise ValueError(f"{label}.devices[{index}].identity_sha256 is invalid")
        for field, maximum in (("friendly_name", 256), ("class", 128), ("status", 64)):
            value = device.get(field)
            if not isinstance(value, str) or len(value) > maximum:
                raise ValueError(f"{label}.devices[{index}].{field} is invalid")
        problem_code = device.get("problem_code")
        if problem_code is not None and (
            isinstance(problem_code, bool) or not isinstance(problem_code, int)
        ):
            raise ValueError(f"{label}.devices[{index}].problem_code is invalid")
        if not isinstance(device.get("problem_reported"), bool):
            raise ValueError(f"{label}.devices[{index}].problem_reported must be boolean")

    packages = snapshot.get("packages")
    if not isinstance(packages, list) or len(packages) > 256:
        raise ValueError(f"{label}.packages must contain at most 256 records")
    if any(not isinstance(package, Mapping) for package in packages):
        raise ValueError(f"{label}.packages entries must be objects")

    total = len(devices)
    ok_count = sum(
        device["status"].casefold() == "ok" and not device["problem_reported"]
        for device in devices
    )
    problem_count = sum(device["problem_reported"] for device in devices)
    derived = {
        "total_devices": total,
        "ok_devices": ok_count,
        "problem_devices": problem_count,
        "other_status_devices": total - ok_count - problem_count,
        "devices_with_class": sum(bool(device["class"]) for device in devices),
        "devices_with_identity": sum(bool(device["identity_sha256"]) for device in devices),
        "audited_packages": len(packages),
        "valid_packages": sum(package.get("valid") is True for package in packages),
    }
    if dict(summary) != derived:
        raise ValueError(f"{label}.summary does not match its device/package records")

    declared_digest = snapshot.get("snapshot_sha256")
    if not isinstance(declared_digest, str) or _SHA256_PATTERN.fullmatch(declared_digest) is None:
        raise ValueError(f"{label}.snapshot_sha256 must be a lowercase SHA-256 digest")
    payload = dict(snapshot)
    payload.pop("snapshot_sha256")
    try:
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} is not canonical JSON data: {error}") from error
    actual_digest = hashlib.sha256(canonical).hexdigest()
    if not hmac.compare_digest(declared_digest, actual_digest):
        raise ValueError(f"{label}.snapshot_sha256 fingerprint mismatch")

    return dict(sorted(normalized.items()))


def oplage_metrics(snapshot: Any) -> dict[str, float]:
    """Validate the complete OPlague snapshot v1 and return sorted metrics."""
    return validate_oplage_snapshot(snapshot)


def compare_oplage_snapshots(
    reference: Any, candidate: Any, native_library: str | os.PathLike[str] | None = None
) -> dict[str, Any]:
    """Compare OPlague snapshot metric maps without changing either input."""
    left = oplage_metrics(reference)
    right = oplage_metrics(candidate)
    if left.keys() != right.keys():
        missing = sorted(left.keys() - right.keys())
        extra = sorted(right.keys() - left.keys())
        raise ValueError(f"profile dimensions differ; candidate missing={missing}, extra={extra}")

    dimensions = list(left)
    reference_values = [left[name] for name in dimensions]
    candidate_values = [right[name] for name in dimensions]
    python_distance = metric_space.euclidean_distance(reference_values, candidate_values)
    distance_backend = "reaper-python"
    distance = python_distance
    native_details: dict[str, Any] | None = None

    if native_library is not None:
        native_path = str(native_library)
        distance = pytyliki_distance(reference_values, candidate_values, native_path)
        distance_backend = "pytyliki-c-abi-v1"
        native_details = {
            "library": str(Path(native_path).expanduser().resolve()),
            "abi_version": 1,
        }

    components = {
        name: {
            "reference": left[name],
            "candidate": right[name],
            "difference": right[name] - left[name],
        }
        for name in dimensions
    }
    result: dict[str, Any] = {
        "schema": REAPER_COMPARISON_SCHEMA,
        "mode": "read_only",
        "reference_snapshot_sha256": reference.get("snapshot_sha256"),
        "candidate_snapshot_sha256": candidate.get("snapshot_sha256"),
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "euclidean_distance": distance,
        "python_euclidean_distance": python_distance,
        "distance_backend": distance_backend,
        "components": components,
    }
    if native_details is not None:
        result["native_backend"] = native_details
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    result["report_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result
