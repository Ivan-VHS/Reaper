# Reaper Processor Control Plane v1

**Status:** executable Reaper policy contracts; privileged CPU backends remain target work.  
**Scope:** DAK kernel policy, Pytyliki processor workstation and Reaper systems-language tooling.

## Purpose

The processor control plane describes the complete software-visible processor surface through versioned contracts. It covers inventory, topology, execution cores and blocks, logical CPUs, threads, scheduling, affinity, interrupts, timers, caches, NUMA locality, ISA/vector state, power and thermal policy, PMU access, virtualization, security features, microcode provenance, debugging, verification, revisions, live update, rollback, telemetry and deterministic replay.

The library is named `stdlib/processor_control.rpr`. Its executable functions validate descriptors, state transitions, resource partitioning, evidence and update admission. They are policy functions, not privileged instructions.

## Ownership across the ecosystem

| Project | Owns | Must not claim |
|---|---|---|
| Reaper | Canonical schemas, Reaper language API, contract validation, IR/ABI evolution and conformance fixtures | Direct hardware writes without a target adapter |
| DAK | Kernel-side core lifecycle, scheduler, interrupt and power-policy enforcement when native backends exist | AP startup, context switches, APIC routing or live patching before those backends are implemented |
| Pytyliki | Native C11 processor inventory, measurements, profile analysis and evidence capture | Changing host scheduling, affinity, voltage, frequency, firmware or microcode by policy alone |

The same logical vocabulary is used in all three projects. Each implementation retains its own owner and trust boundary.

## Canonical processor model

A processor snapshot is positional in v1 and must migrate to typed records when aggregate syntax and native lowering are available:

`[schema, snapshot_id, architecture, vendor, packages, dies, cores, logical_threads, online_threads, generation, features, source]`

A core descriptor is:

`[core_id, package_id, die_id, cluster_id, class, state, online_threads, thread_ids, revision_id, generation]`

A thread descriptor is:

`[tid, pid, priority, deadline_ns, stack_bytes, state, affinity, generation]`

Every count is a non-negative integer with explicit cardinality relationships. Topology generations change when CPU hotplug or a source rescan changes the observed topology. A stale descriptor must not be reused for a newer generation.

## Control domains

1. **Processor and topology:** vendor, family/model/stepping, package/die/cluster/core/thread topology, NUMA nodes, cache hierarchy, memory-controller locality and instruction-set features.
2. **Core and execution blocks:** core class, online state, SMT siblings, execution units, pipelines, vector units, branch prediction, cache slices and resource-sharing domains. Block-level controls are adapter-defined; generic policy cannot invent hardware registers.
3. **Execution and concurrency:** thread lifecycle, affinity, priorities, deadlines, preemption, cooperative work budgets, load balancing, CPU isolation, interrupt affinity and deterministic replay.
4. **Timing and interrupts:** invariant time source selection, local timers, APIC mode, interrupt routing, interrupt-safe work queues, watchdog deadlines and bounded interrupt-disabled sections.
5. **Memory locality:** cache-sharing groups, NUMA placement, first-touch policy, page migration hints, TLB invalidation coordination and DMA ownership. These require memory-manager and device adapters.
6. **Performance and power:** P-state/boost policy, frequency caps, idle states, energy counters, PMU sessions, thermal headroom, throttling and emergency cooling response. Requests are advisory until a trusted platform driver accepts them.
7. **ISA and security:** CPUID/feature inventory, OS-enabled vector state, crypto instructions, virtualization extensions, mitigation capabilities and microcode provenance. Hardware support alone never implies OS-state support.
8. **Lifecycle and maintenance:** CPU hotplug, core quarantine, bounded debug sessions, firmware/microcode revision inventory, signed kernel/core revisions, staged activation, rollback and forensic audit.

## State and version rules

Core lifecycle: `offline → starting → online → draining → offline`; failures and quarantine are explicit branches. A core may be released only after runnable work, active interrupts, held locks and DMA leases are all zero.

A revision uses semantic version fields, an ABI major, source digest, parent reference, monotonic generation and lifecycle state: `draft → verified → staged → active → retired`. Rejected candidates never become active. An update candidate must preserve the ABI major or provide an explicit migration contract.

Verification evidence binds the candidate identity to total/passed/failed tests, coverage basis points, duration, artifact SHA-256 and verifier identity. Zero failures are mandatory for activation. Benchmarks are separate evidence and cannot replace correctness checks.

## Live development and rollback

"Live" means a controlled staged deployment, not arbitrary mutation of running machine code:

1. Build an immutable candidate and compute its digest.
2. Verify source, IR, ABI, stack bounds, interrupt safety and compatibility.
3. Run deterministic, differential, stress, fuzz and target-specific tests.
4. Check signature and provenance.
5. Wait for a declared safe point; drain affected work and reach quiescence.
6. Confirm the rollback artifact, state migration and recovery route.
7. Stage the candidate. A privileged backend may activate it atomically at a supported boundary.
8. Observe health within a bounded window; commit the revision or restore the previous known-good version.
9. Write an append-only local audit record with generation and evidence references.

The v1 Reaper function returns an admission decision such as `admit-stage-only`; it never patches instructions or changes CPU registers itself.

## Capability model

Operations are classified as `read-only`, `policy-preview`, `kernel-backend`, `architecture-adapter`, `firmware-adapter` or `privileged-adapter`. The caller must supply a capability for privileged actions. Capabilities are scoped by operation, target, generation and expiry, with deny-by-default behavior and an audit trail.

Safe defaults: read-only discovery, local telemetry, bounded measurements, no implicit network, no firmware writes, no voltage/frequency change, no driver installation and no unbounded debug capture.

## Verification and acceptance gates

- Schema and topology cardinality checks.
- Core and thread state-transition tests, including invalid transitions.
- Affinity bounds, uniqueness and topology-generation checks.
- Work-partition conservation and deterministic tie-breaking.
- Scheduler fairness/deadline and priority-inversion fixtures.
- Interrupt and preemption stress under bounded execution.
- PMU/thermal/power adapter fault injection.
- Version monotonicity, ABI compatibility and signature rejection.
- Live-update quiescence, rollback and crash-recovery tests.
- Scalar/reference versus optimized implementation parity.
- Reproducible fixtures, local audit evidence and tree-walk/VM parity.
- Target qualification for each CPU family, firmware mode and platform backend.

The conformance fixture is `examples/processor_control.rpr`. CI must check and execute it with both the tree-walk and VM engines.

## Maturity statement

The Reaper module and its fixture establish the v1 contract surface. They do not by themselves implement AP startup, a preemptive multiprocessor scheduler, power-management drivers, PMU access, hardware debug, signed firmware updates or kernel live patching. DAK and Pytyliki must report those features against native source, tests and target evidence rather than inherit a status from this policy library.
