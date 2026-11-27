# Reaper Processor Control Plane v1

**Status:** executable Reaper policy contracts plus a native C17 control library and capability-gated platform adapter ABI.  
**Scope:** DAK kernel policy, Pytyliki processor workstation and Reaper systems-language tooling.

## Purpose

The processor control plane describes the full software-visible CPU surface through versioned contracts. It covers inventory, topology, execution cores and blocks, logical CPUs, threads, scheduling, affinity, interrupts, timers, caches, NUMA locality, ISA/vector state, power and thermal policy, PMU access, virtualization, security features, microcode provenance, debugging, verification, revisions, live updates, rollback, telemetry and deterministic replay.

The Reaper language module is `stdlib/processor_control.rpr`. It validates descriptors, scheduling decisions, state transitions, resource partitioning, evidence and update admission. The native C17 ABI is `include/reaper/processor_control.h` with implementation in `src/processor_control.c`.

## Native C17 surface

The native implementation provides:

- topology-generation and logical-CPU uniqueness validation;
- affinity checks and stable priority/deadline selection with deterministic round-robin tie-breaking;
- thread lifecycle validation and CPU drain/quiescence gates;
- AP startup readiness admission;
- bounded context-frame validation using 8-byte stack alignment, including the x86-64 System V initial-entry shape;
- ABI, digest, verification-evidence and monotonic revision checks;
- capability-gated frequency caps and power-profile callbacks;
- bounded debug capture with timeout and output-size enforcement;
- image/signature verification callbacks, immutable patch staging tickets, separate activation and rollback calls.

The C API is compiled into `reaper_core`. Its native conformance suite is `tests/test_processor_control.c` and is registered as `native-processor-control` in CTest.

This establishes native C parity for the processor-control library. It does **not** establish full Reaper language compiler/runtime parity: the C17 compiler track remains a separate implementation milestone.

## Platform adapter contract

`ReaperProcessorPlatformOps` is the only route from policy to an external privileged implementation. Its capabilities are separate for power control, debug capture, patch staging, patch activation and patch rollback.

- Frequency and power requests include a CPU ID, validated bounds/profile and topology generation.
- Debug capture is bounded to a 64 KiB maximum output buffer and a 60-second maximum timeout.
- Artifact verification receives the exact immutable image bytes, expected digest and signature. The platform verifier must hash those bytes and verify the signature; a caller-supplied boolean is not accepted as cryptographic proof.
- Patch staging is limited to 16 MiB, returns an opaque adapter ticket and does not activate executable code.
- Activation is a separate operation and requires a safe point and quiescence.
- Rollback references the adapter-issued ticket and a known-good generation older than the staged generation.

The callback interface does not itself implement MSR writes, a PMU driver, a debug-register engine or kernel text patching. Those require a trusted platform backend which owns the hardware-specific validation and recovery path. Missing capability bits or callbacks fail closed.

## Ownership across the ecosystem

| Project | Owns | Must not claim |
|---|---|---|
| Reaper | Canonical schemas, language policy, native control-plane algorithms, ABI validation and platform adapter contracts | A privileged effect when no trusted backend is installed |
| DAK | Kernel scheduling and CPU lifecycle integration, architecture startup, native context switching and privileged CPU services as they are implemented | AP startup, preemptive SMP or kernel hotpatch completion before the entry path and hardware backends use the primitives |
| Pytyliki | Native C11 processor inventory, measurements, profile analysis and evidence capture | Changing host scheduling, affinity, voltage, frequency, firmware or microcode |

## Canonical processor model

A processor snapshot is positional in v1 and migrates to typed records when aggregate syntax and native lowering are available:

`[schema, snapshot_id, architecture, vendor, packages, dies, cores, logical_threads, online_threads, generation, features, source]`

A core descriptor is:

`[core_id, package_id, die_id, cluster_id, class, state, online_threads, thread_ids, revision_id, generation]`

A thread descriptor is:

`[tid, pid, priority, deadline_ns, stack_bytes, state, affinity, generation]`

Every count is a non-negative integer with explicit cardinality relationships. Topology generations change when CPU hotplug or a source rescan changes the observed topology. A stale descriptor must not be reused for a newer generation.

## Live development and rollback

"Live" means a controlled staged deployment, not arbitrary mutation of running machine code:

1. Build an immutable candidate and compute its digest.
2. Verify source, IR, ABI, stack bounds, interrupt safety and compatibility.
3. Run deterministic, differential, stress, fuzz and target-specific tests.
4. Ask the trusted platform verifier to hash the exact candidate image and verify its signature.
5. Wait for a declared safe point; drain affected work and reach quiescence.
6. Confirm the rollback artifact, state migration and recovery route.
7. Stage the candidate and retain the platform-issued ticket.
8. Activate only through the separate capability-gated callback.
9. Observe health within a bounded window; commit the revision or use the rollback callback to restore the previous known-good version.
10. Write an append-only local audit record with generation and evidence references.

The Reaper policy function returns an admission decision; the native adapter ABI exposes explicit stages. Neither silently performs arbitrary patching.

## Verification and acceptance gates

- Schema and topology cardinality checks.
- Core and thread state-transition tests, including invalid transitions.
- Affinity bounds, uniqueness and topology-generation checks.
- Work-partition conservation and deterministic tie-breaking.
- AP startup prerequisite and failure-path tests.
- Context-frame alignment and bounds.
- Debug time/output caps and capability denial.
- Power/frequency range validation and missing-adapter denial.
- Version monotonicity, ABI compatibility and artifact signature rejection.
- Live-update quiescence, staging, activation and rollback fault injection.
- Reaper tree-walk/VM fixture parity and C17 conformance tests.
- Target qualification for each CPU family, firmware mode and platform backend.

The Reaper-language conformance fixture is `examples/processor_control.rpr`. CI checks and executes it with the tree-walk and VM engines. Native C tests are run by CMake/CTest.

## Maturity statement

Reaper now supplies an executable contract surface and a native C17 control-plane library. Platform callbacks are interfaces, not a built-in hardware driver. DAK and Pytyliki must report privileged behavior against their own native source, tests and target evidence; they do not inherit an implemented status from Reaper policy.
