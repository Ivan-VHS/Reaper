# Reaper Robotics Core v1 — Language Contracts

## Purpose and compatibility

This specification defines Reaper's source-level semantic contracts for safety-oriented robotics software. It extends the existing Embedded C Workbench and Typed Registry direction without changing current grammar or claiming native AOT support for new constructs. The first executable form is a Reaper-written standard-library contract module in stdlib/robotics_core.rpr, using currently supported Reaper constructs.

## Mathematical model

A robotics program is modeled as a state transition system:

- System state X contains actuator targets, sensor estimates, health, thermal/load state, timing counters and tuning generation.
- An input event E is timestamped and typed by its physical dimension.
- A control step is the deterministic transition F(X, E, Δt) → (X', O, D), where O is a complete actuator frame and D is a set of diagnostics.
- A contract is a predicate over the state, event, transition or output. Invalid transitions return ERR and do not publish partial state.
- Hardware effects are explicit capabilities; the Reaper model never itself maps physical addresses or writes a device.

Dimension vector: D = (L, M, T, I, A), for length, mass, time, current and angle. Addition/comparison requires equal vectors. Multiplication adds exponents; division subtracts exponents. Unit conversion changes scale but not dimension. The core named units include mm, m, rad, Nm, A, mA, m/s, rad/s and W. Integer/fixed-point values are preferred in deterministic control paths.

Timing model: release r, completion c, deadline d, period P, execution budget B and jitter allowance J. A sample passes iff c ≤ d, observed execution ≤ B, and absolute release deviation ≤ J. This is an observation contract, not static WCET proof.

Sensor model: a sample x_s captured at t_s is aligned to control time t_c with bounded prediction x(t_c) = x_s + v_s(t_c − t_s). Samples beyond a configured maximum horizon, in the future, or without a valid velocity bound are rejected.

## Thirteen contracts

1. @deadline/@budget: explicit period, release, completion, deadline, execution and jitter values; enforceable runtime checks and compile-time analysis as a future compiler milestone.
2. Physical units: dimension-safe addition/comparison, explicit conversions, derived dimensions and bounded arithmetic.
3. Isolation: separate criticality domains with CPU and bus quota accounting; the target scheduler/HAL enforces actual isolation.
4. Actuator transaction: prepare and validate a complete frame; publish only at a tick boundary. Physical multi-device atomicity is an adapter capability, not a software assumption.
5. @failsafe: fault classes map to an explicit action, timeout and escalation policy.
6. Shadow step: compare predicted and observed state, tolerance and residual.
7. Thermal/load budget: integrate bounded current/load exposure, temperature trip and deterministic derating.
8. Sensor latency: timestamp capture, validate age and predict to common control time.
9. DMA lifecycle: CPU-owned → device-owned → completed → CPU-owned; Reaper's ownership checker must reject overlapping CPU access while device-owned.
10. Flight recorder: fixed capacity, bounded event schema, no allocation/blocking in critical producer path and explicit overflow policy.
11. Calibration: raw bounds, offset, gain, maximum step, stuck detection and explicit invalid-sample policy.
12. Live tuning: complete versioned parameter set, checksum/integrity validation and atomic generation switch between ticks.
13. Graceful limp: fault-mask-to-mode transition table, approved fallback modes only, bounded speed/torque and explicit stop profile.

## Execution and hardware boundary

The initial .rpr module is executable on the reference Reaper interpreter, not a new compiler grammar. Its predicates and transition helpers are normative contract code. Static ownership enforcement, first-class dimensional types, WCET path analysis, MIR lowering and generated target code remain compiler milestones. HAL operations require explicit capabilities, and platform adapters remain responsible for cache coherency, interrupts, timers, scheduler policy, physical output and failsafe hardware.

## Acceptance

- All 13 contracts have a Reaper-language model and deterministic positive/negative assertions.
- The module runs under the existing reference runtime without changing grammar.
- Invalid dimensions, deadlines, state transitions, sensor times and safety policies produce ERR.
- Reaper and Pytyliki use matching identifiers, units, ownership transitions and safety boundaries.
- Documentation distinguishes implemented language contracts from future compiler capabilities and board-qualified guarantees.
