# Reaper Robotics Core — Reaper Contract Implementation Plan

> For agentic workers: implement task-by-task, use the existing Reaper self-hosting conformance pattern, and verify all Reaper files before completion.

**Goal:** Add an executable Reaper-language robotics contract model for all 13 capabilities.
**Architecture:** One focused Reaper standard-library module models dimensions, timing, resource quotas, actuator state transitions, failsafe policies, sensor prediction, shadow residuals, thermal limits, DMA ownership, recorder schema, calibration, tuning generations and limp modes. It uses existing grammar; no speculative syntax is introduced.
**Tech Stack:** Reaper .rpr, existing reference Interpreter, current self-hosting conformance suite and native CMake checks.
**Spec:** docs/ROBOTICS_CORE_V1.md

## Global Constraints

- Reaper source is the canonical contract layer; do not add Python implementations of robotics behavior.
- Preserve existing .rpr grammar and source compatibility.
- Use explicit OK/ERR results; invalid transitions must not mutate prior state.
- Represent dimensions as (L, M, T, I, A); reject incompatible addition/comparison.
- Keep MMIO, DMA programming, timers and physical outputs behind granted capabilities and platform adapters.
- Do not describe the reference interpreter contract module as native compiler support or hardware qualification.

## Review Focus

- Negative and very large integer values in conversion, multiplication and time arithmetic.
- Equal-to-deadline and equal-to-tolerance boundary decisions.
- DMA double-submit, early reclaim and use while device-owned.
- Sensor samples with future capture times or age beyond horizon.
- Failsafe and limp tables missing a fault mapping or requesting an unqualified action.

## File Map

- Create stdlib/robotics_core.rpr with pure validation and deterministic state-transition functions.
- Create examples/robotics_core.rpr as a readable robot-control contract example.
- Modify tests/test_self_hosting.py to register the new Reaper module using the existing interpreter conformance helper.
- Update docs/ROBOTICS_CORE_V1.md and docs/EMBEDDED_C_WORKBENCH.md with implementation boundaries.

---

### Task 1: Dimensional quantity model

Add unit descriptors, dimension equality, checked conversion and derived dimensions for mm, m, rad, Nm, A, mA, m/s, rad/s and W.
Assertions: valid same-dimension addition; explicit scale conversion; rejection of m + rad; derived Nm × rad/s dimension equals power; overflow returns ERR.

### Task 2: Timing and resource-domain contracts

Add deadline/budget evaluation and period-scoped CPU/bus quota accounting.
Assertions: exact deadline accepted, late completion rejected, execution overrun rejected, jitter overrun rejected, exhausted quota rejected and window rollover reset.

### Task 3: Actuator transaction and failsafe contracts

Add immutable staged frames, validation and commit/rollback transition helpers, plus fault-to-action policy validation.
Assertions: full frame commit, incomplete frame rejection, invalid channel rejection, rollback preserves previous committed frame, unmapped fault rejection and invalid action rejection.

### Task 4: Shadow, thermal, sensor and calibration contracts

Add fixed-point shadow residual comparison, bounded thermal integration/derating, capture-time sensor prediction and raw-sample calibration/range validation.
Assertions: residual inside/outside tolerance, thermal threshold/derating boundaries, future/stale sensor rejection, valid predicted state, out-of-range calibration and stuck/step detection.

### Task 5: DMA, recorder, tuning and limp contracts

Add DMA ownership transitions, fixed-capacity recorder descriptor/overflow model, generation/checksum tuning validation and approved fallback-mode selection.
Assertions: double DMA submit rejected, early reclaim rejected, recorder overflow policy explicit, stale tuning generation rejected, partial parameter update rejected and unconfigured limp fallback rejected.

### Task 6: Example, conformance integration and documentation

Add a complete Reaper .rpr example and register stdlib/robotics_core.rpr in the existing self-hosting conformance suite.
Assertions: module emits ROBOTICS_CORE_OK exactly once; all negative assertions pass; source compatibility and current hardware boundaries remain documented.

## Commit sequence

1. Add the Reaper contract module and failing conformance registration.
2. Implement the dimension and timing contract functions.
3. Implement motion, fault and sensor/thermal contracts.
4. Implement DMA, recorder, tuning and limp contracts.
5. Add the example and documentation; run the existing Reaper CTest suite and full self-hosting suite.
6. Review all changed files and open a draft PR; do not merge.
