"""Read-only ingestion and normalization of OPlague GPU telemetry v1.

This module reads an explicitly selected JSON artifact. It never probes hardware,
executes an external command, installs a driver or grants a device capability.
The SHA-256 check protects canonical payload integrity; it is not publisher
authentication or build provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .federation import read_json, write_json

OPLAGE_GPU_SCHEMA = "oplage.gpu-telemetry.v1"
MAX_GPU_COUNT = 16
MAX_REASON_LENGTH = 512
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOP_LEVEL_FIELDS = {
    "schema", "snapshot_id", "captured_at", "source", "available",
    "reason", "controls_performed", "gpus", "snapshot_sha256",
}
_SOURCE_FIELDS = {"provider", "mode"}
_GPU_FIELDS = {
    "name", "driver_version", "temperature_c", "utilization_pct",
    "memory_used_mib", "memory_total_mib", "power_w",
    "graphics_clock_mhz", "memory_clock_mhz",
}


def _canonical_digest(payload: dict[str, Any]) -> str:
    """Compute v1 digest over canonical JSON without snapshot_sha256."""
    unsigned = dict(payload)
    unsigned.pop("snapshot_sha256", None)
    encoded = json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _optional_integer(value: Any, label: str, minimum: int, maximum: int) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer or null")
    if not minimum <= value <= maximum:
        raise ValueError(f"{label} must be within [{minimum}, {maximum}]")
    return value


def _optional_number(value: Any, label: str, minimum: float, maximum: float) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a number or null")
    number = float(value)
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{label} must be finite and within [{minimum}, {maximum}]")
    return value


def _normalize_gpu(gpu: Any, index: int) -> list[Any]:
    label = f"gpus[{index}]"
    if not isinstance(gpu, dict) or set(gpu) != _GPU_FIELDS:
        raise ValueError(f"{label} must contain exactly the nine v1 fields")

    name = gpu["name"]
    driver = gpu["driver_version"]
    if not isinstance(name, str) or not name or len(name) > 256:
        raise ValueError(f"{label}.name must contain 1..256 characters")
    if not isinstance(driver, str) or not driver or len(driver) > 128:
        raise ValueError(f"{label}.driver_version must contain 1..128 characters")

    temperature = _optional_integer(gpu["temperature_c"], f"{label}.temperature_c", -20, 150)
    utilization = _optional_integer(gpu["utilization_pct"], f"{label}.utilization_pct", 0, 100)
    memory_used = _optional_integer(gpu["memory_used_mib"], f"{label}.memory_used_mib", 0, 2_147_483_647)
    memory_total = _optional_integer(gpu["memory_total_mib"], f"{label}.memory_total_mib", 1, 2_147_483_647)
    power = _optional_number(gpu["power_w"], f"{label}.power_w", 0, 10_000)
    graphics_clock = _optional_integer(gpu["graphics_clock_mhz"], f"{label}.graphics_clock_mhz", 0, 20_000)
    memory_clock = _optional_integer(gpu["memory_clock_mhz"], f"{label}.memory_clock_mhz", 0, 20_000)

    if memory_used is not None and memory_total is not None and memory_used > memory_total:
        raise ValueError(f"{label}.memory_used_mib cannot exceed memory_total_mib")

    unknown = "unknown"
    return [
        name, driver,
        temperature if temperature is not None else unknown,
        utilization if utilization is not None else unknown,
        memory_used if memory_used is not None else unknown,
        memory_total if memory_total is not None else unknown,
        power if power is not None else unknown,
        graphics_clock if graphics_clock is not None else unknown,
        memory_clock if memory_clock is not None else unknown,
    ]


def normalize_oplage_gpu_snapshot(snapshot: Any) -> list[Any]:
    """Validate raw OPlague v1 JSON and return the DAKOS Reaper record.

    Normalized record:
      [schema, snapshot_id, captured_at, provider, mode, available, reason,
       controls_performed, digest_verified, gpu_rows]

    Sensor JSON nulls become the literal "unknown"; no values are estimated.
    """
    label = "OPlague GPU snapshot"
    if not isinstance(snapshot, dict):
        raise TypeError(f"{label} must be a JSON object")
    if set(snapshot) != _TOP_LEVEL_FIELDS:
        missing = sorted(_TOP_LEVEL_FIELDS - set(snapshot))
        extra = sorted(set(snapshot) - _TOP_LEVEL_FIELDS)
        raise ValueError(f"{label} fields are invalid; missing={missing}, extra={extra}")
    if snapshot["schema"] != OPLAGE_GPU_SCHEMA:
        raise ValueError(f"{label}.schema must be {OPLAGE_GPU_SCHEMA}")

    snapshot_id = snapshot["snapshot_id"]
    if not isinstance(snapshot_id, str):
        raise TypeError(f"{label}.snapshot_id must be a UUID string")
    try:
        parsed_id = uuid.UUID(snapshot_id)
    except (ValueError, AttributeError) as error:
        raise ValueError(f"{label}.snapshot_id must be a valid UUID") from error
    if str(parsed_id) != snapshot_id:
        raise ValueError(f"{label}.snapshot_id must use canonical lowercase UUID text")

    captured_at = snapshot["captured_at"]
    if not isinstance(captured_at, str):
        raise TypeError(f"{label}.captured_at must be date-time text")
    try:
        captured = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label}.captured_at must be ISO 8601 date-time") from error
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError(f"{label}.captured_at must include a timezone")

    source = snapshot["source"]
    if not isinstance(source, dict) or set(source) != _SOURCE_FIELDS:
        raise ValueError(f"{label}.source must contain provider and mode only")
    if source["provider"] != "nvidia-smi" or source["mode"] != "read_only":
        raise ValueError(f"{label}.source must identify nvidia-smi in read_only mode")

    available = snapshot["available"]
    if not isinstance(available, bool):
        raise TypeError(f"{label}.available must be boolean")
    if snapshot["controls_performed"] is not False:
        raise ValueError(f"{label}.controls_performed must be false")

    reason = snapshot["reason"]
    if available:
        if reason is not None:
            raise ValueError(f"{label}.reason must be null when telemetry is available")
    elif not isinstance(reason, str) or not reason or len(reason) > MAX_REASON_LENGTH:
        raise ValueError(f"{label}.reason must explain why telemetry is unavailable")

    raw_gpus = snapshot["gpus"]
    if not isinstance(raw_gpus, list) or len(raw_gpus) > MAX_GPU_COUNT:
        raise ValueError(f"{label}.gpus must contain at most {MAX_GPU_COUNT} records")
    if available and not raw_gpus:
        raise ValueError(f"{label}.gpus must contain at least one device when available")
    if not available and raw_gpus:
        raise ValueError(f"{label}.gpus must be empty when unavailable")

    normalized_gpus = [_normalize_gpu(item, index) for index, item in enumerate(raw_gpus)]

    declared_digest = snapshot["snapshot_sha256"]
    if not isinstance(declared_digest, str) or _SHA256.fullmatch(declared_digest) is None:
        raise ValueError(f"{label}.snapshot_sha256 must be a lowercase SHA-256 digest")
    if not hmac.compare_digest(declared_digest, _canonical_digest(snapshot)):
        raise ValueError(f"{label}.snapshot_sha256 fingerprint mismatch")

    # Digest verification is payload-integrity evidence only. It does not
    # authenticate the publisher or the build that produced this file.
    return [
        OPLAGE_GPU_SCHEMA, snapshot_id, captured_at,
        source["provider"], source["mode"], available,
        reason if reason is not None else "", False, True, normalized_gpus,
    ]


def load_oplage_gpu_snapshot(path: str | Path) -> list[Any]:
    """Read an explicitly selected bounded JSON file and normalize it."""
    return normalize_oplage_gpu_snapshot(read_json(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and normalize a read-only OPlague GPU telemetry snapshot."
    )
    parser.add_argument("input", type=Path, help="explicit OPlague v1 JSON snapshot")
    parser.add_argument("--output", type=Path, required=True, help="normalized JSON output path")
    args = parser.parse_args(argv)
    normalized = load_oplage_gpu_snapshot(args.input)
    write_json(args.output, normalized)
    print(f"validated {len(normalized[9])} GPU record(s); wrote {args.output}")
    print("sha256_verified=true; publisher_authenticated=false; controls_performed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
