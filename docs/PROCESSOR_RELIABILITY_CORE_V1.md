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


## RAS event and periodicity layer

The core now includes versioned, positional RAS provider/event/series records. A provider must be explicitly read-only and declare only observation operations. Events retain boot identity, provider identity, resource scope, classification, confidence, monotonic timestamp and raw-record reference. No process/thread owner is inferred from a package-, core- or memory-controller-scoped record.

ras_series_record rejects mixed boot/provider/resource/fault series, duplicate or out-of-order monotonic timestamps and counter overflow. It retains at most eight recent timestamps and reports how many older samples were dropped. ras_periodicity_analyze requires at least three strictly increasing timestamps, checks each interval against a 1000-second bound and returns mean period, interval spread in permille and a periodic/drifting/irregular class. Its deterministic thresholds are a model contract, not a hardware failure predictor.

ras_recovery_action produces advisory decisions only: observe, warn-and-collect, request an OS recovery path, request operator/OS review, or defer fatal cases to the kernel. It never retries fatal errors and never writes registers, MMIO, firmware, voltage, frequency or scheduler state. The RAS_CLASSIFY bytecode instruction (opcode 65, RULE domain, SERVICE role) encodes a bounded fault kind, repeat count and explicit confidence/OS/rollback flags; decoding and role/domain validation happen before the decision is returned.

Hardware-specific WHEA, Linux EDAC/MCE and Apple event adapters remain outside this language core. They must preserve source provenance and provide verified classification before a live event can enter this model. Copper/electromigration and nano-cell equations in the same core remain deterministic simulation, not physical repair.


## Processor control, AP/SMP and native adapter contracts

The Reaper core now defines an implementation matrix for the nine requested processor/RAS subsystems, plus executable state machines and admission predicates. Reaper owns input validation, topology-generation increments and stale-route checks, AP startup readiness, IPI route policy, timer quantum decisions, MCG_CAP-bounded MSR allowlists, normalized MCA event classification, page-recovery preconditions and the diagnostics wire envelope.

- AP/SMP: ap_startup_valid, ap_startup_readiness, ap_startup_transition and ap_smp_admit_cpu enforce boot identity, BSP readiness, GDT/IDT, unique stack, per-CPU data, local-controller readiness, trampoline evidence and topology generation. The native kernel still has to discover ACPI processors, allocate AP resources and send INIT/SIPI. State transitions to startup-sent/online require adapter acknowledgements; production must authenticate those acknowledgements in the trusted kernel boundary because the Reaper token is a structural policy record, not a cryptographic proof.
- APIC/IPI/timer: apic_route_valid, apic_ipi_decision, timer_preemption_decision and timer_preemption_admission validate endpoints, vector, mask, interrupt state and quantum expiry. Actual APIC MMIO, local timer programming and IPI delivery require a kernel-control adapter.
- MCA/MSR: mca_msr_allowlisted permits only IA32_MCG_CAP/STATUS/CTL and only the first MCG_CAP-reported machine-check banks for read-only access. mca_event_valid consumes normalized flags rather than pretending Reaper can safely decode arbitrary 64-bit status values. mca_handler_decision refuses invalid records and defers corrupt processor context to the kernel fatal path. A privileged x86 adapter must perform the actual RDMSR and exception entry.
- Page recovery: page_recovery_decision refuses pinned/referenced pages, requires a page-scope match to the MCA evidence, verified copy for dirty pages, valid uncorrected address evidence and rollback readiness. Actual page offlining, replacement allocation, reverse-map updates and TLB shootdown belong to the native memory manager.
- Linux EDAC/MCE: linux_edac_provider_descriptor describes a read-only sysfs/tracefs provider. It is deliberately available=false until a Linux adapter is attached and qualified.
- Apple Swift: apple_swift_ras_adapter_descriptor defines the Swift/C ABI boundary for OS-published diagnostics. It does not claim raw MCA MSR access on Apple platforms.
- Rust native RAS: rust_native_ras_adapter_descriptor defines a versioned DABI64 adapter contract, not an installed Rust driver.
- TypeScript diagnostics: typescript_diagnostic_valid and typescript_diagnostic_export validate read-only diagnostic packets. A UI/client transport is not part of the kernel and cannot receive privileged operations.
- Physical copper/silicon repair: physical_repair_assessment always reports physical damage as not software-repairable. Software may isolate a resource and request qualified laboratory inspection or component replacement.

The bytecode VM now accepts opcodes 66-70 for AP startup, IPI routing, timer preemption, MCA handling and page-recovery admission. They return typed policy decisions after normal domain/role verification. They do not execute RDMSR, WRMSR, MMIO, INIT/SIPI, APIC writes, page-table edits or hardware repair. No opcode can bypass adapter authority.


### Provider normalization contracts

The Linux EDAC adapter contract now has a pure counter-snapshot normalizer. It records a first snapshot as a baseline, computes only monotonic CE/UE deltas, rejects counter resets and cross-boot/resource comparisons, and emits common RAS envelopes. A UE counter without a poisoned page address is deliberately normalized as software-suspected/supporting evidence, not as a confirmed page-level MCA record.

The Apple Swift contract accepts a versioned OS-diagnostics record and maps its explicit source severity/confidence into the shared RAS envelope. The Rust contract validates a DABI64 packet sequence and requires an attached read-only adapter before ingestion. These are executable Reaper ABI checks and normalizers; the actual sysfs/tracefs reader, Swift system API client and Rust FFI binary remain separate native deliverables.


## Requested subsystem status matrix

| Subsystem | Reaper implementation | Native platform status |
|---|---|---|
| Real AP startup and SMP | Startup state machine, BSP readiness, topology generation and admission contracts | INIT/SIPI/AP trampoline and live SMP still require DuckOS kernel work |
| APIC, IPI and timer preemption | Route, vector, endpoint, mask, quantum and adapter-authority policies | APIC MMIO, interrupt entry, IPI delivery and context switch are not invoked by Reaper |
| Kernel MCA handler and MCA MSR | Event normalizer, context-corrupt policy, MCG_CAP-bounded read allowlist | RDMSR and #MC handler require privileged x86 kernel code |
| Automatic OS page recovery | Poison evidence, resource-scope matching, pin/refcount, verified-copy and rollback gates | Page offlining, replacement, reverse-map update and TLB shootdown require memory-manager code |
| Linux EDAC/MCE provider | Counter-snapshot baseline/delta normalizer and common RAS envelope | Linux sysfs/tracefs reader remains unattached |
| Apple Swift provider | Swift ABI descriptor and diagnostics normalizer | Swift system API adapter remains unattached |
| Rust native RAS adapter | DABI64 packet validation and read-only ingest contract | Rust FFI implementation remains unattached |
| TypeScript diagnostics interface | Versioned read-only packet validation/export | TypeScript client transport remains unattached |
| Physical copper/silicon repair | Explicit impossibility classification and isolate/inspect/replace recommendation | Requires physical laboratory process or component replacement; no software repair |

