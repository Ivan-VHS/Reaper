"""Read-only verifier and diagnostic adapter for DuckOS hardware snapshots."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import re
import sys
from typing import Any

INVENTORY_SCHEMA = "duckos.hardware-inventory.v1"
REPORT_SCHEMA = "reaper.duckos-hardware-audit.v1"
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024
_MAX_DEVICES = 10_000
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HARDWARE_ID = re.compile(r"^0x[0-9a-f]{4}$")
_STATUSES = {"driver_bound", "driver_missing", "device_problem"}
_BUSES = {"pci", "usb", "pnp"}
_TOP_FIELDS = {"schema", "captured_utc", "source", "summary", "devices", "snapshot_sha256"}
_SOURCE_FIELDS = {"provider", "mode", "platform", "architecture"}
_SUMMARY_FIELDS = {"total_devices", "driver_bound", "driver_missing", "device_problem"}
_DEVICE_FIELDS = {
    "identity_sha256", "bus", "vendor_id", "device_id", "device_class",
    "friendly_name", "driver", "status",
}


class DuckOSInventoryError(ValueError):
    """Raised when a DuckOS hardware snapshot is malformed or has changed."""


def _text(value: Any, field: str, limit: int, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > limit:
        raise DuckOSInventoryError(f"{field} must be text of at most {limit} characters")
    if not allow_empty and not value.strip():
        raise DuckOSInventoryError(f"{field} must not be empty")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise DuckOSInventoryError(f"{field} contains a control character")
    return value


def _optional_hardware_id(value: Any, field: str) -> str | None:
    if value is None:
        return None
    text = _text(value, field, 6)
    if not _HARDWARE_ID.fullmatch(text):
        raise DuckOSInventoryError(f"{field} must be null or a lowercase 0x-prefixed 16-bit ID")
    return text


def _snapshot_digest(snapshot: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    try:
        encoded = json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DuckOSInventoryError(f"snapshot cannot be canonicalised: {error}") from error
    return hashlib.sha256(encoded).hexdigest()


def audit_snapshot(snapshot: Any) -> dict[str, Any]:
    """Validate a DuckOS v1 inventory and return a bounded diagnostic report."""
    if not isinstance(snapshot, dict) or set(snapshot) != _TOP_FIELDS:
        raise DuckOSInventoryError(f"snapshot fields must be exactly {sorted(_TOP_FIELDS)}")
    if snapshot.get("schema") != INVENTORY_SCHEMA:
        raise DuckOSInventoryError(f"schema must be {INVENTORY_SCHEMA}")

    captured_utc = _text(snapshot.get("captured_utc"), "captured_utc", 64)
    try:
        timestamp = datetime.fromisoformat(captured_utc.replace("Z", "+00:00"))
    except ValueError as error:
        raise DuckOSInventoryError("captured_utc must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise DuckOSInventoryError("captured_utc must include a timezone")

    source = snapshot.get("source")
    if not isinstance(source, dict) or set(source) != _SOURCE_FIELDS:
        raise DuckOSInventoryError(f"source fields must be exactly {sorted(_SOURCE_FIELDS)}")
    if source.get("provider") != "duckos-host-inventory" or source.get("mode") != "read_only":
        raise DuckOSInventoryError("source must identify the DuckOS read-only host inventory provider")
    platform_name = source.get("platform")
    if platform_name not in {"linux", "windows"}:
        raise DuckOSInventoryError("source.platform must be linux or windows")
    architecture = _text(source.get("architecture"), "source.architecture", 64)

    summary = snapshot.get("summary")
    if not isinstance(summary, dict) or set(summary) != _SUMMARY_FIELDS:
        raise DuckOSInventoryError(f"summary fields must be exactly {sorted(_SUMMARY_FIELDS)}")
    for field in _SUMMARY_FIELDS:
        value = summary.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= _MAX_DEVICES:
            raise DuckOSInventoryError(f"summary.{field} must be an integer from 0 to {_MAX_DEVICES}")

    devices = snapshot.get("devices")
    if not isinstance(devices, list) or len(devices) > _MAX_DEVICES:
        raise DuckOSInventoryError(f"devices must be an array of at most {_MAX_DEVICES} entries")

    actual_counts = {status: 0 for status in _STATUSES}
    audited_devices = []
    for index, device in enumerate(devices):
        prefix = f"devices[{index}]"
        if not isinstance(device, dict) or set(device) != _DEVICE_FIELDS:
            raise DuckOSInventoryError(f"{prefix} fields must be exactly {sorted(_DEVICE_FIELDS)}")
        identity = _text(device.get("identity_sha256"), f"{prefix}.identity_sha256", 64)
        if not _SHA256.fullmatch(identity):
            raise DuckOSInventoryError(f"{prefix}.identity_sha256 must be a lowercase SHA-256 digest")
        bus = device.get("bus")
        if bus not in _BUSES:
            raise DuckOSInventoryError(f"{prefix}.bus must be pci, usb or pnp")
        vendor_id = _optional_hardware_id(device.get("vendor_id"), f"{prefix}.vendor_id")
        device_id = _optional_hardware_id(device.get("device_id"), f"{prefix}.device_id")
        device_class = _text(device.get("device_class"), f"{prefix}.device_class", 128)
        friendly_name = _text(device.get("friendly_name"), f"{prefix}.friendly_name", 256)
        driver_value = device.get("driver")
        driver = None if driver_value is None else _text(driver_value, f"{prefix}.driver", 128)
        status = device.get("status")
        if status not in _STATUSES:
            raise DuckOSInventoryError(f"{prefix}.status is not a supported device state")
        if status == "driver_bound" and driver is None:
            raise DuckOSInventoryError(f"{prefix} claims a bound driver but has no driver name")
        if status == "driver_missing" and driver is not None:
            raise DuckOSInventoryError(f"{prefix} claims a missing driver but includes a driver name")

        actual_counts[status] += 1
        audited_devices.append({
            "identity_sha256": identity,
            "bus": bus,
            "vendor_id": vendor_id,
            "device_id": device_id,
            "device_class": device_class,
            "friendly_name": friendly_name,
            "driver": driver,
            "status": status,
        })

    total = len(audited_devices)
    if summary["total_devices"] != total:
        raise DuckOSInventoryError("summary.total_devices does not match the device array")
    for status, count in actual_counts.items():
        if summary[status] != count:
            raise DuckOSInventoryError(f"summary.{status} does not match the device array")

    supplied_digest = snapshot.get("snapshot_sha256")
    if not isinstance(supplied_digest, str) or not _SHA256.fullmatch(supplied_digest):
        raise DuckOSInventoryError("snapshot_sha256 must be a lowercase SHA-256 digest")
    calculated_digest = _snapshot_digest(snapshot)
    if not hmac.compare_digest(supplied_digest, calculated_digest):
        raise DuckOSInventoryError("snapshot SHA-256 does not match its contents")

    findings = []
    for device in audited_devices:
        if device["status"] == "driver_missing":
            findings.append({
                "code": "DUCKOS-DRIVER-MISSING",
                "severity": "warning",
                "device_sha256": device["identity_sha256"],
                "device": device["friendly_name"],
                "message": "No driver binding was reported by the host inventory.",
                "recommended_next_step": "Check the hardware revision, OS support and vendor-signed driver package.",
            })
        elif device["status"] == "device_problem":
            findings.append({
                "code": "DUCKOS-DEVICE-PROBLEM",
                "severity": "error",
                "device_sha256": device["identity_sha256"],
                "device": device["friendly_name"],
                "message": "The host reports a device problem state.",
                "recommended_next_step": "Inspect the operating-system device error and its signed driver package.",
            })

    return {
        "schema": REPORT_SCHEMA,
        "valid": True,
        "status": "attention_required" if findings else "clean",
        "captured_utc": captured_utc,
        "source": {
            "provider": source["provider"],
            "platform": platform_name,
            "architecture": architecture,
        },
        "snapshot_sha256": supplied_digest,
        "summary": {
            "total_devices": total,
            **actual_counts,
            "findings": len(findings),
        },
        "metrics": {
            "driver_coverage_ratio": round(actual_counts["driver_bound"] / total, 4) if total else None,
            "device_problem_ratio": round(actual_counts["device_problem"] / total, 4) if total else None,
        },
        "findings": findings,
        "devices": audited_devices,
        "execution_performed": False,
        "disk_writes_performed": False,
        "drivers_changed": False,
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate properties instead of silently accepting the last value."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuckOSInventoryError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise DuckOSInventoryError(f"non-finite JSON constant is not permitted: {value}")


def audit_file(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.is_symlink():
        raise DuckOSInventoryError("snapshot path must be a regular, non-symlink file")

    descriptor: int | None = None
    try:
        # O_NOFOLLOW closes the symlink race on platforms that expose it. The
        # bounded read remains the final guard on every supported platform.
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(source, flags)
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise DuckOSInventoryError("snapshot path must be a regular file")
            raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            raise DuckOSInventoryError(
                f"snapshot exceeds the {MAX_SNAPSHOT_BYTES}-byte input limit"
            )
        try:
            snapshot = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
        except UnicodeDecodeError as error:
            raise DuckOSInventoryError("snapshot is not valid UTF-8") from error
        except json.JSONDecodeError as error:
            raise DuckOSInventoryError(f"snapshot is not valid JSON: {error}") from error
    except DuckOSInventoryError:
        raise
    except OSError as error:
        raise DuckOSInventoryError(f"cannot read snapshot: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return audit_snapshot(snapshot)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaper-duckos-audit",
        description="Validate a DuckOS read-only hardware snapshot and report driver-binding issues.",
    )
    parser.add_argument("snapshot", type=Path, help="DuckOS hardware-inventory.v1 JSON file")
    parser.add_argument("--output", type=Path, help="write the audit report to this path")
    args = parser.parse_args(argv)
    try:
        report = audit_file(args.snapshot)
        encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            if args.output.expanduser().resolve() == args.snapshot.expanduser().resolve():
                raise DuckOSInventoryError("audit output must not overwrite the input snapshot")
            args.output.write_text(encoded, encoding="utf-8", newline="\n")
        else:
            print(encoded, end="")
        return 0
    except (DuckOSInventoryError, OSError, TypeError, ValueError) as error:
        print(f"reaper-duckos-audit: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
