"""Recommend a game resource profile from a read-only hardware sample."""
from __future__ import annotations

from typing import Any

from .common import optional_number, require_object


def run(payload: dict[str, Any]) -> dict[str, Any]:
    hardware = require_object(payload.get("hardware"), "hardware")
    gpu_temp = optional_number(hardware, "gpu_temp_c", 0.0, minimum=-20.0, maximum=150.0)
    cpu_load = optional_number(hardware, "cpu_load_pct", 0.0, minimum=0.0, maximum=100.0)
    vram_free = optional_number(hardware, "vram_free_mb", 0.0, minimum=0.0)

    if gpu_temp > 85.0:
        profile = {"preset": "thermal_safe", "fps_cap": 60, "io_priority": "normal",
                   "reason": "gpu_temperature_above_85c"}
    elif cpu_load > 80.0 and vram_free < 1024.0:
        profile = {"preset": "balanced_low_vram", "fps_cap": 90, "io_priority": "high",
                   "reason": "cpu_pressure_and_low_free_vram"}
    else:
        profile = {"preset": "ultra_low_latency", "fps_cap": 144, "io_priority": "normal",
                   "reason": "no_guardrail_threshold_triggered"}

    return {
        "profile": profile,
        "observed": {"gpu_temp_c": gpu_temp, "cpu_load_pct": cpu_load, "vram_free_mb": vram_free},
        "applied": False,
        "scope": "recommendation_only",
    }
