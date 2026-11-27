# Processor Reliability Core v1

**Status:** executable Reaper-source model with conformance fixture. Hardware operations remain simulated or adapter-gated.

The core lives in `stdlib/processor_reliability.rpr`. The end-to-end fixture is `examples/processor_reliability.rpr`.

## Scope

The module composes six bounded subsystems:

| Subsystem | Public surface | Contract |
|---|---|---|
| Formal Core | `valid_integer`, `checked_add`, `checked_multiply`, `quantity`, `convert_quantity` | Safe-integer arithmetic, finite bounds, explicit physical dimensions |
| Execution Core | `type_role_matrix`, `validate_construct`, `run_construct`, `bytecode_encode`, `bytecode_decode`, `execute_bytecode` | Exactly 20 registered type/role pairs; strict opcode/domain validation |
| Repair Core | `new_state`, `repair_spend`, `repair_forecast`, `reserve_spend`, `root_capability_descriptor`, `repair_recover` | Finite shared budget, reserve-backed recovery, explicit exhaustion and safe degradation |
| Physical Core | `silicon_domain`, `silicon_advance`, `silicon_barrier`, `hardware_register_snapshot`, `copper_evaluate`, `copper_age`, `copper_channel`, `copper_channel_age`, `nano_cell`, `nano_repair`, `stream_state`, `stream_advance` | Bounded deterministic silicon, stream, simulated register/barrier, copper RC, electromigration and nano-cell models |
| Correction Core | `correction_step`, `apply_correction` | Signed feedback, bounded gain and step, no intentional overshoot, residual-error convergence checks |
| Pytyliki | `trace_checksum`, `replay_validate`, `run_load_test`, `replay_load_test`, `pytyliki_report` | Deterministic trace, repeat-execution comparison, bounded load run, replay verification and versioned report envelope |

The source uses the currently supported Reaper grammar and positional list records. It does not introduce unsupported parser-level struct, enum, MMIO or IRQ syntax.

This package currently targets Reaper's reference interpreter/VM. The present native AOT compiler does not yet lower list operations, imports/exports or dynamic module dispatch used here, so this fixture is not advertised as an AOT-native binary. A later AOT port must first implement those language features and pass reference/native conformance tests.

## State and records

`new_state(capacity, low_watermark, mode, local_reserves, initial_phase_error_ps)` returns `[ok, state, diagnostic]`.

The state record is versioned and has the following slots:

| Index | Field |
|---:|---|
| 0–1 | Magic `RPC` and schema version |
| 2 | Simulated cycle counter |
| 3–5 | Initial capacity, remaining repair budget, low watermark |
| 6 | `production` or `test` mode |
| 7–11 | Fault-injection enabled, period, duty, phase and activation count |
| 12–13 | Signed residual phase error and cumulative absolute correction |
| 14–15 | Executed step and service invocation counters |
| 16 | Kernel lifecycle/degradation status |
| 17 | Local repair-cell reserves |
| 18 | Injected test-fault count |
| 19 | Simulated barrier/fence counter |

Do not mutate state records outside the module. Every transition returns a replacement record; `state_valid` checks the full shape and bounds.

The simulated register snapshot contains ten positional values in this order: `CYCLE_CNT`, `REPAIR_BUDGET`, `REPAIR_LOW_WATERMARK`, `FAULT_PERIOD`, `FAULT_DUTY`, `FAULT_CTRL`, `CU_BUS_CTRL`, `NANO_ARRAY_CMD`, `SKEW_CORRECT_PS` and `BARRIER_FENCE_COUNT`. The fault-control mask is `EN=0x01 | MONUMENTAL=0x02 | INSTANT=0x04 | PERIODIC_ACTIVE=0x08`; the active snapshot is `0x0F`. Copper and nano command values are simulated profile values only.

## Execution and bytecode

The type/role matrix contains four roles for each of `RULE`, `BOOT`, `START`, `ROOT` and `SCENARIO`. `validate_matrix_coverage` rejects missing combinations and non-20 fixture sets.

RPR-BC words are represented as two unsigned 32-bit integers:

- `high32 = opcode * 2^24 + domain * 2^16 + operandA`
- `low32 = operandB * 2^16 + flags`

Both operands and flags must fit `u16`; each word must fit `u32`. Unknown opcode and domain values fail decoding. The supported opcodes are `0x10`, `0x11`, `0x12`, `0x20`, `0x21`, `0x30`, `0x31` and `0x40`. For `0x10`, flag bit zero selects `OPERAND`; otherwise it dispatches `OPERATION`. `0x11` dispatches `COMMAND` and `0x12` dispatches `SERVICE`.

The copper-tune instruction evaluates a deterministic RC fixture from its operands; the nano-pulse instruction consumes a bounded local repair-cell fixture. These are model operations, not bus writes.

## Repair and fault policy

A repair debit is clamped to the remaining budget. Crossing the low watermark is a one-time state transition while periodic injection is active. Re-activating an already-active scenario is idempotent and does not increment the activation counter.

- In `production` mode, low reserve moves the state to `safe-degraded`; fault injection is denied.
- In `test` mode, crossing the watermark may enable bounded periodic fault injection. The injected fault is explicitly synthetic and is counted in the trace.
- Re-entering a low-budget state does not repeatedly increment the activation counter.
- The forecast is advisory and never reserves or spends resources.
- Production state created with `remaining_budget <= low_watermark` starts directly in `safe-degraded`. That state blocks new `START` constructs. `repair_recover` can restore a production state only with a revision-bound, mode-bound, scope-bound ROOT capability descriptor and a sufficient local reserve; the reserve is debited by exactly the credited amount. Recovery increments the step, service and simulated barrier counters, invalidating the old revision-bound descriptor. Recovery above the low watermark returns the lifecycle to `ready`.

The fault window is `((cycle - phase) % period) < duty`. Period and duty are validated before activation.

## Physical and correction models

Copper resistance uses the supplied geometry and material values:

`R_mOhm = resistivity_nOhm_m * length_um * 1,000,000 / area_nm2`

The first-order RC delay is:

`delay_ps = R_mOhm * capacitance_fF / 1,000,000`

Electromigration wear is a bounded deterministic stress estimate using squared current density, elapsed cycles and a temperature factor. It is a comparative model, not a process-qualified lifetime prediction.

Correction uses a signed error `e`, gain `g` in permille and maximum step `s`. The applied step is bounded by `min(abs(e) * g / 1000, s)`, with a one-unit minimum for nonzero errors. Its sign opposes the error. The verifier checks:

`abs(residual_error) <= abs(previous_error)`

A monotonic step is not evidence of physical convergence outside the model. Real clock/phase correction requires measured feedback and a qualified target-specific controller.

## Pytyliki report

`pytyliki_report` returns the versioned schema `pytyliki.processor-reliability.v1`, including sample count, deterministic checksum, remaining budget, injected-fault count, scenario activation count, absolute residual error, lifecycle status and evidence quality.

The report explicitly labels the measurements as `simulated` and includes the limitation that no hardware writes, scheduler changes or voltage changes occurred. Synthetic fixtures must not be mixed with observed processor telemetry.

## Verification

From the Reaper repository root:

```sh
python -m reaper --check examples/processor_reliability.rpr
python -m reaper examples/processor_reliability.rpr
```

Load-test runs are bounded to 5,000 steps to stay within the reference runtime execution budget.

The fixture asserts all 20 matrix entries, operand/operation/command/service bytecode dispatch, bytecode round-trip and rejection, arithmetic/unit invariants, production fault-injection denial, safe degradation and blocked dispatch, revision-bound reserve-backed ROOT recovery, silicon thermal guards, simulated registers/barriers, stream correction, copper RC and wear calculations, nano-cell shortfall, signed correction, trace validation, a second full deterministic load execution with complete trace comparison and the Pytyliki report schema.

CI must require these exact output lines:

- `REAPER_PROCESSOR_RELIABILITY:PASS`
- `TYPE_ROLE_COVERAGE:20/20`
- `PYTYLIKI_REPLAY:PASS`

## Hardware boundary

This package does not map physical addresses, write MMIO, program CPU registers, alter scheduling/affinity/voltage/frequency, install firmware or drivers, register real interrupts or repair physical processor faults. The register snapshot and barriers are simulated descriptors. The barrier counter is a logical dispatch/fence accounting field; it is not a CPU memory-fence instruction or a measured hardware cycle counter. ROOT capability validation here is a structural simulation contract, not a cryptographic identity proof: a production host must issue and verify the capability through a trusted OS/driver authorization boundary. A future real backend must be a separate capability-gated OS/driver adapter with target/ABI validation, real memory-ordering primitives, audit records and hardware-in-the-loop qualification.
