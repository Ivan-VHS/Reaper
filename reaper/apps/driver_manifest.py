"""Build a read-only driver update plan using strict semantic-version comparison."""
from __future__ import annotations

import re
from typing import Any

from .common import ApplicationInputError, require_array, require_object, require_text

_VERSION = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def _version(value: str, label: str) -> tuple[Any, ...]:
    match = _VERSION.fullmatch(value)
    if not match:
        raise ApplicationInputError(f"{label} must use semantic version MAJOR.MINOR.PATCH")
    major, minor, patch = (int(match.group(index)) for index in (1, 2, 3))
    normalized = value[1:] if value.startswith("v") else value
    core = normalized.split("+", 1)[0]
    prerelease = core.split("-", 1)[1] if "-" in core else ""
    if not prerelease:
        return (major, minor, patch, 1, ())
    identifiers: list[tuple[int, Any]] = []
    for identifier in prerelease.split("."):
        if not identifier or (identifier.isdecimal() and len(identifier) > 1 and identifier.startswith("0")):
            raise ApplicationInputError(f"{label} contains an invalid semantic-version prerelease identifier")
        identifiers.append((0, int(identifier)) if identifier.isdecimal() else (1, identifier))
    return (major, minor, patch, 0, tuple(identifiers))


def run(payload: dict[str, Any]) -> dict[str, Any]:
    devices = require_array(payload, "devices")
    plan: list[dict[str, Any]] = []
    skipped = 0
    for index, item in enumerate(devices):
        device = require_object(item, f"devices[{index}]")
        enabled = device.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ApplicationInputError(f"devices[{index}].enabled must be a boolean")
        if not enabled:
            skipped += 1
            continue
        hardware_id = require_text(device.get("hw_id"), f"devices[{index}].hw_id")
        name = require_text(device.get("name", hardware_id), f"devices[{index}].name")
        latest = require_text(device.get("latest_version"), f"devices[{index}].latest_version")
        latest_key = _version(latest, f"devices[{index}].latest_version")
        current_raw = device.get("driver_version", "")
        if not isinstance(current_raw, str):
            raise ApplicationInputError(f"devices[{index}].driver_version must be text")
        current = current_raw.strip()
        if current:
            current_key = _version(current, f"devices[{index}].driver_version")
            needs_update = current_key < latest_key
        else:
            needs_update = True
        if needs_update:
            priority = device.get("bus_priority", 100)
            if isinstance(priority, bool) or not isinstance(priority, int):
                raise ApplicationInputError(f"devices[{index}].bus_priority must be a whole number")
            plan.append({
                "hw_id": hardware_id,
                "name": name,
                "current_version": current or None,
                "target_version": latest,
                "bus_priority": priority,
            })

    plan.sort(key=lambda item: (item["bus_priority"], item["hw_id"]))
    return {
        "plan": plan,
        "counts": {"devices": len(devices), "updates": len(plan), "disabled": skipped},
        "installation_performed": False,
    }
