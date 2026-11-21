# Atomic-Quantum 133 — Reaper reference runtime

Reaper carries the language-facing reference contract for 133 atomic/quantum operation IDs. Its Python runtime can host bounded, deterministic classical simulations and expose them to language tooling; the C17 track is not treated as quantum hardware execution.

## Families

| Ordinals | Family | Scope |
|---|---|---|
| 001–022 | State | Qubit/atom initialization, normalization, rotations and level models |
| 023–044 | Entanglement | Bell/GHZ/W construction and correlation measurements |
| 045–066 | Measurement | Projective sampling, readout, feedback and telemetry |
| 067–088 | Noise / ECC | Channels, syndrome primitives and code helpers |
| 089–110 | Atomic dynamics | Lattice, potential and transport models |
| 111–133 | Algorithms / telemetry | Algorithmic kernels and health metrics |

## Contracts and limits

- Canonical manifest: `schemas/atomic-quantum-functions.v1.json`; schema: `schemas/atomic-quantum-functions.v1.schema.json`.
- Simulation uses a bounded state vector, finite-value validation, norm checks and seeded measurements.
- Function IDs are stable API names. The registry distinguishes implemented simulation kernels from catalogue-only research contracts; registration alone never implies numerical validation.
- QCS contracts and Reaper execution remain software-side. No device is discovered, calibrated or controlled implicitly.

See [QCS](../reaper/qcs.py), [Reaper architecture](ARCHITECTURE.md) and [NOO TAH architecture](NOO_TAH.md).
