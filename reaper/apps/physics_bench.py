"""Calculate kinetic energy, mechanical work and an energy-efficiency ratio."""
from __future__ import annotations

from typing import Any

from .common import ApplicationInputError, optional_number, require_number, require_object


def run(payload: dict[str, Any]) -> dict[str, Any]:
    run_data = require_object(payload.get("run"), "run")
    mass = require_number(run_data.get("mass_kg"), "run.mass_kg", minimum=0.0)
    if mass == 0.0:
        raise ApplicationInputError("run.mass_kg must be greater than zero")
    speed = require_number(run_data.get("speed_m_s"), "run.speed_m_s", minimum=0.0)
    input_energy = require_number(run_data.get("input_energy_j"), "run.input_energy_j", minimum=0.0)
    if input_energy == 0.0:
        raise ApplicationInputError("zero_input_energy")
    kinetic = 0.5 * mass * speed * speed
    if kinetic > input_energy:
        raise ApplicationInputError("invalid_output_energy")
    efficiency = (kinetic / input_energy) * 100.0
    work: float | None = None
    if ("force_n" in run_data) != ("distance_m" in run_data):
        raise ApplicationInputError("force_n and distance_m must be supplied together")
    if "force_n" in run_data:
        force = require_number(run_data.get("force_n"), "run.force_n")
        distance = require_number(run_data.get("distance_m"), "run.distance_m")
        work = force * distance
    return {
        "kinetic_energy_j": round(kinetic, 9),
        "work_j": None if work is None else round(work, 9),
        "efficiency_pct": round(efficiency, 6),
        "input_energy_j": input_energy,
        "valid": True,
    }
