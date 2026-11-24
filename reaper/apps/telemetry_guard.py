"""Validate sensor readings and split accepted records from rejected samples."""
from __future__ import annotations

from typing import Any
import math

from .common import require_array, require_number, require_object


def run(payload: dict[str, Any]) -> dict[str, Any]:
    readings = require_array(payload, "readings")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for index, item in enumerate(readings):
        record_id: Any = index
        try:
            row = require_object(item, f"readings[{index}]")
            record_id = row.get("id", index)
            temperature = require_number(row.get("temp_c"), f"readings[{index}].temp_c")
            voltage = require_number(row.get("voltage_v"), f"readings[{index}].voltage_v")
            current = require_number(row.get("current_a"), f"readings[{index}].current_a")
            if not -50.0 <= temperature <= 150.0:
                raise ValueError("temp_out_of_range")
            if not 0.0 < voltage <= 48.0:
                raise ValueError("voltage_invalid")
            if current < 0.0:
                raise ValueError("current_invalid")
            power = voltage * current
            if not math.isfinite(power):
                raise ValueError("power_overflow")
            accepted.append({
                "id": record_id,
                "temp_c": temperature,
                "power_w": round(power, 6),
            })
        except (TypeError, ValueError) as error:
            rejected.append({"id": record_id, "index": index, "reason": str(error)})

    return {
        "accepted": accepted,
        "rejected": rejected,
        "counts": {"received": len(readings), "accepted": len(accepted), "rejected": len(rejected)},
    }
