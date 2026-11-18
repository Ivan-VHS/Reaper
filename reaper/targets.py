"""Host target metadata and explicit backend capability reporting.

This module does not select a cross-compiler or claim native machine-code support.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TargetInfo:
    system: str
    machine: str
    architecture: str
    execution_model: str
    interpreter_backend: str
    python_host_compiler: str
    native_codegen: bool
    notes: tuple[str, ...]


def detect_target(
    system: str | None = None,
    machine: str | None = None,
    python_compiler: str | None = None,
) -> TargetInfo:
    """Return host metadata; optional values make detection deterministic in tests."""
    host_system = system if system is not None else platform.system()
    host_machine = machine if machine is not None else platform.machine()
    host_compiler = python_compiler if python_compiler is not None else platform.python_compiler()
    normalized = host_machine.strip().lower().replace("_", "-")
    is_e2k = normalized in {"e2k", "elbrus", "mcst-e2k"} or normalized.startswith("e2k-")

    if is_e2k:
        return TargetInfo(
            system=host_system,
            machine=host_machine,
            architecture="e2k",
            execution_model="VLIW",
            interpreter_backend="python-tree-walk",
            python_host_compiler=host_compiler,
            native_codegen=False,
            notes=(
                "E2K was inferred from the host machine identifier reported by Python.",
                "This does not identify the MCST LCC compiler or validate a processor feature.",
                "Reaper currently interprets source through Python; native E2K code generation is not implemented.",
            ),
        )

    return TargetInfo(
        system=host_system,
        machine=host_machine,
        architecture=normalized or "unknown",
        execution_model="not-inferred",
        interpreter_backend="python-tree-walk",
        python_host_compiler=host_compiler,
        native_codegen=False,
        notes=(
            "Architecture is host metadata reported by Python platform.machine().",
            "No native compiler backend or cross-target selection is performed.",
        ),
    )
