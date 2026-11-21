"""Bounded, deterministic classical quantum-state simulator for Reaper.

This module is a state-vector reference model. It does not access quantum hardware.
Advanced catalogue entries without a reviewed kernel are reported as catalogued-only.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

MAX_QUBITS = 10
MAX_AMPLITUDES = 1 << MAX_QUBITS
_TOLERANCE = 1e-10
_CATALOGUE = Path(__file__).with_name("atomic_quantum_catalogue.v1.json")

class AtomicQuantumError(ValueError):
    """Invalid state, operation, or simulation parameter."""

class KernelUnavailableError(AtomicQuantumError):
    """The function is catalogued but has no reviewed numerical kernel yet."""

@dataclass
class QuantumRegister:
    qubits: int
    amplitudes: list[complex]

    def copy(self) -> "QuantumRegister":
        return QuantumRegister(self.qubits, list(self.amplitudes))

    def validate(self, normalized: bool = True) -> None:
        if isinstance(self.qubits, bool) or not 1 <= self.qubits <= MAX_QUBITS:
            raise AtomicQuantumError(f"qubits must be in 1..{MAX_QUBITS}")
        if len(self.amplitudes) != 1 << self.qubits:
            raise AtomicQuantumError("amplitude vector size does not match qubit count")
        if any(not (math.isfinite(a.real) and math.isfinite(a.imag)) for a in self.amplitudes):
            raise AtomicQuantumError("amplitudes must be finite")
        norm = math.fsum(abs(a) ** 2 for a in self.amplitudes)
        if norm <= 0.0 or not math.isfinite(norm):
            raise AtomicQuantumError("state norm must be finite and positive")
        if normalized and abs(norm - 1.0) > 1e-8:
            raise AtomicQuantumError("state vector must be normalized")

def _probability(value: Any, name: str = "probability") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise AtomicQuantumError(f"{name} must be finite and in [0, 1]")
    return result

def _qubit(register: QuantumRegister, target: Any) -> int:
    register.validate()
    if isinstance(target, bool) or not isinstance(target, int) or not 0 <= target < register.qubits:
        raise AtomicQuantumError("target qubit is outside the register")
    return target

def zero_state(qubits: int = 1) -> QuantumRegister:
    if isinstance(qubits, bool) or not isinstance(qubits, int) or not 1 <= qubits <= MAX_QUBITS:
        raise AtomicQuantumError(f"qubits must be an integer in 1..{MAX_QUBITS}")
    amplitudes = [0j] * (1 << qubits)
    amplitudes[0] = 1 + 0j
    return QuantumRegister(qubits, amplitudes)

def basis_state(qubits: int, index: int) -> QuantumRegister:
    register = zero_state(qubits)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(register.amplitudes):
        raise AtomicQuantumError("basis index is outside the register")
    register.amplitudes = [0j] * len(register.amplitudes)
    register.amplitudes[index] = 1 + 0j
    return register

def normalize(register: QuantumRegister) -> QuantumRegister:
    register.validate(normalized=False)
    norm = math.sqrt(math.fsum(abs(a) ** 2 for a in register.amplitudes))
    if not math.isfinite(norm) or norm <= 0:
        raise AtomicQuantumError("cannot normalize a zero or non-finite state")
    register.amplitudes = [a / norm for a in register.amplitudes]
    register.validate()
    return register

def reset(register: QuantumRegister) -> QuantumRegister:
    register.validate(normalized=False)
    register.amplitudes = [0j] * len(register.amplitudes)
    register.amplitudes[0] = 1 + 0j
    return register

def _pairs(qubits: int, target: int) -> Iterable[tuple[int, int]]:
    mask = 1 << target
    for base in range(1 << qubits):
        if not base & mask:
            yield base, base | mask

def hadamard(register: QuantumRegister, target: int = 0) -> QuantumRegister:
    target = _qubit(register, target)
    scale = 1 / math.sqrt(2)
    for zero, one in _pairs(register.qubits, target):
        a0, a1 = register.amplitudes[zero], register.amplitudes[one]
        register.amplitudes[zero] = (a0 + a1) * scale
        register.amplitudes[one] = (a0 - a1) * scale
    register.validate()
    return register

def phase_rotate(register: QuantumRegister, target: int, theta: float) -> QuantumRegister:
    target = _qubit(register, target)
    if isinstance(theta, bool) or not isinstance(theta, (int, float)) or not math.isfinite(float(theta)):
        raise AtomicQuantumError("theta must be a finite real angle")
    phase = complex(math.cos(float(theta)), math.sin(float(theta)))
    for _, one in _pairs(register.qubits, target):
        register.amplitudes[one] *= phase
    register.validate()
    return register

def pauli_x(register: QuantumRegister, target: int = 0) -> QuantumRegister:
    target = _qubit(register, target)
    for zero, one in _pairs(register.qubits, target):
        register.amplitudes[zero], register.amplitudes[one] = register.amplitudes[one], register.amplitudes[zero]
    register.validate()
    return register

def pauli_z(register: QuantumRegister, target: int = 0) -> QuantumRegister:
    target = _qubit(register, target)
    for _, one in _pairs(register.qubits, target):
        register.amplitudes[one] *= -1
    register.validate()
    return register

def cnot(register: QuantumRegister, control: int, target: int) -> QuantumRegister:
    control = _qubit(register, control)
    target = _qubit(register, target)
    if control == target:
        raise AtomicQuantumError("control and target qubits must differ")
    control_mask, target_mask = 1 << control, 1 << target
    for index in range(len(register.amplitudes)):
        if index & control_mask and not index & target_mask:
            other = index | target_mask
            register.amplitudes[index], register.amplitudes[other] = register.amplitudes[other], register.amplitudes[index]
    register.validate()
    return register

def swap(register: QuantumRegister, left: int, right: int) -> QuantumRegister:
    left = _qubit(register, left)
    right = _qubit(register, right)
    if left == right:
        return register
    a, b = 1 << left, 1 << right
    for index in range(len(register.amplitudes)):
        if not index & a and index & b:
            other = index ^ a ^ b
            register.amplitudes[index], register.amplitudes[other] = register.amplitudes[other], register.amplitudes[index]
    register.validate()
    return register

def bell_pair() -> QuantumRegister:
    register = zero_state(2)
    hadamard(register, 0)
    cnot(register, 0, 1)
    return register

def ghz_state(qubits: int = 3) -> QuantumRegister:
    register = zero_state(qubits)
    hadamard(register, 0)
    for target in range(1, qubits):
        cnot(register, 0, target)
    return register

def probabilities(register: QuantumRegister) -> list[float]:
    register.validate()
    return [abs(amplitude) ** 2 for amplitude in register.amplitudes]

def measure_z(register: QuantumRegister, target: int = 0, *, seed: int = 0,
              sample: float | None = None) -> int:
    target = _qubit(register, target)
    if sample is None:
        sample = random.Random(seed).random()
    value = float(sample)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise AtomicQuantumError("measurement sample must be in [0, 1)")
    probability_one = math.fsum(abs(register.amplitudes[i]) ** 2
                                for i in range(len(register.amplitudes)) if i & (1 << target))
    outcome = 1 if value < probability_one else 0
    mask = 1 << target
    register.amplitudes = [a if bool(i & mask) == bool(outcome) else 0j
                           for i, a in enumerate(register.amplitudes)]
    normalize(register)
    return outcome

def dephase(register: QuantumRegister, target: int = 0, probability: float = 1.0,
            *, seed: int = 0) -> QuantumRegister:
    target = _qubit(register, target)
    p = _probability(probability)
    if random.Random(seed).random() < p:
        pauli_z(register, target)
    return register

def amplitude_damp(register: QuantumRegister, target: int = 0, gamma: float = 0.0,
                   *, seed: int = 0) -> QuantumRegister:
    target = _qubit(register, target)
    g = _probability(gamma, "gamma")
    p1 = math.fsum(abs(register.amplitudes[i]) ** 2
                   for i in range(len(register.amplitudes)) if i & (1 << target))
    jump_probability = min(1.0, g * p1)
    jump = random.Random(seed).random() < jump_probability
    mask = 1 << target
    updated = list(register.amplitudes)
    if jump:
        scale = math.sqrt(g)
        for zero, one in _pairs(register.qubits, target):
            updated[zero], updated[one] = register.amplitudes[one] * scale, 0j
    else:
        scale = math.sqrt(1.0 - g)
        for zero, one in _pairs(register.qubits, target):
            updated[zero], updated[one] = register.amplitudes[zero], register.amplitudes[one] * scale
    register.amplitudes = updated
    return normalize(register)

def fidelity(left: QuantumRegister, right: QuantumRegister) -> float:
    left.validate(); right.validate()
    if left.qubits != right.qubits:
        raise AtomicQuantumError("registers must have equal qubit counts")
    overlap = sum(a.conjugate() * b for a, b in zip(left.amplitudes, right.amplitudes))
    return min(1.0, max(0.0, abs(overlap) ** 2))

def telemetry(register: QuantumRegister) -> dict[str, Any]:
    probs = probabilities(register)
    entropy = -math.fsum(p * math.log2(p) for p in probs if p > 0.0)
    return {
        "qubits": register.qubits,
        "norm": math.fsum(probs),
        "measurement_entropy_bits": entropy,
        "purity_pure_state": 1.0,
        "most_probable_basis": max(range(len(probs)), key=probs.__getitem__),
        "max_probability": max(probs),
        "execution_model": "bounded_classical_simulation",
        "quality": "simulated",
    }

# These are the numerical kernels currently covered by conformance tests.
SIMULATED_KERNELS = frozenset({
    "qubit_phase_rotate_02", "atom_ground_reset_03", "state_amplitude_normalize_04",
    "entangle_bell_pair_23", "entangle_ghz_ring_24", "measure_projective_z_45",
    "measure_fidelity_ref_59", "noise_amplitude_damp_69",
})

def function_catalog() -> list[dict[str, Any]]:
    try:
        data = json.loads(_CATALOGUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AtomicQuantumError(f"cannot load atomic quantum catalogue: {error}") from error
    functions = data.get("functions")
    if data.get("function_count") != 133 or not isinstance(functions, list) or len(functions) != 133:
        raise AtomicQuantumError("atomic quantum catalogue must contain exactly 133 functions")
    ids = [item.get("id") for item in functions]
    if len(set(ids)) != 133:
        raise AtomicQuantumError("atomic quantum function IDs must be unique")
    return [{**item, "status": "simulated" if item["id"] in SIMULATED_KERNELS else "catalogued-only"}
            for item in functions]

def get_function(function_id: str) -> dict[str, Any]:
    if not isinstance(function_id, str):
        raise TypeError("function_id must be text")
    for item in function_catalog():
        if item["id"] == function_id:
            return item
    raise AtomicQuantumError(f"unknown atomic quantum function: {function_id!r}")

def require_kernel(function_id: str) -> dict[str, Any]:
    item = get_function(function_id)
    if item["status"] != "simulated":
        raise KernelUnavailableError(f"{function_id} is catalogued but has no reviewed numerical kernel yet")
    return item

__all__ = [
    "MAX_QUBITS", "AtomicQuantumError", "KernelUnavailableError", "QuantumRegister",
    "zero_state", "basis_state", "normalize", "reset", "hadamard", "phase_rotate",
    "pauli_x", "pauli_z", "cnot", "swap", "bell_pair", "ghz_state", "probabilities",
    "measure_z", "dephase", "amplitude_damp", "fidelity", "telemetry",
    "function_catalog", "get_function", "require_kernel", "SIMULATED_KERNELS",
]
