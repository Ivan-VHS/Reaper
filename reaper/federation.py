"""Bounded JSON contracts for read-only OPlague federation."""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from . import metric_space
from .native import pytyliki_distance

OPLAGE_SNAPSHOT_SCHEMA = "oplage.device-snapshot.v1"
REAPER_COMPARISON_SCHEMA = "reaper.oplage-comparison.v1"
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_METRICS = 128


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


def oplage_metrics(snapshot: Any) -> dict[str, float]:
    """Validate and return the normalized metric map from snapshot v1."""
    if not isinstance(snapshot, Mapping):
        raise TypeError("OPlague snapshot must be a JSON object")
    if snapshot.get("schema") != OPLAGE_SNAPSHOT_SCHEMA:
        raise ValueError(f"snapshot schema must be {OPLAGE_SNAPSHOT_SCHEMA}")
    metrics = snapshot.get("metrics")
    if not isinstance(metrics, Mapping) or not 1 <= len(metrics) <= MAX_METRICS:
        raise ValueError(f"snapshot.metrics must contain 1..{MAX_METRICS} entries")

    result: dict[str, float] = {}
    for raw_name, raw_value in metrics.items():
        if not isinstance(raw_name, str) or not raw_name.strip() or len(raw_name) > 128:
            raise ValueError("snapshot contains an invalid metric name")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise TypeError(f"snapshot.metrics.{raw_name} must be a real number")
        try:
            value = float(raw_value)
        except OverflowError as error:
            raise ValueError(f"snapshot.metrics.{raw_name} is outside the numeric range") from error
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"snapshot.metrics.{raw_name} must be finite and within [0, 1]")
        if raw_name in result:
            raise ValueError(f"snapshot contains a duplicate metric: {raw_name}")
        result[raw_name] = value
    return dict(sorted(result.items()))


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
