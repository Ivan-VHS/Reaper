# Pytyliki Processor Fabric → Reaper integration contract v1

**Status:** import and ownership contract only. This document does not claim a live PPF importer, Canonical Typed IR lowering pass or target backend implementation.

## Purpose

Pytyliki Processor Fabric (PPF) is the evidence and process-graph provider. Reaper is the canonical semantic, typed-IR and compiler owner. The boundary is a local, versioned, caller-selected data hand-off; it is not an implicit native FFI call and it does not grant hardware privileges.

This contract composes four existing work streams without duplicating their responsibilities:

- Pytyliki #299: structural Hardware AST and first PPF inventory/process graph.
- Pytyliki #282: processor topology validation, affinity selection, partitioning and operation admission.
- Reaper #406: CPU/thread lifecycle, topology validation, scheduling policy and capability-gated platform adapters.
- Reaper #420: Processor Engineering Platform project/ABI/evidence admission and the current host-only scalar C17 AOT path.

All are separate review streams until their branches are reconciled and merged. A consumer must pin a reviewed schema/version and must not assume an open PR's source is already on either repository's main branch.

## Responsibility split

| Concern | Pytyliki | Reaper |
|---|---|---|
| Host CPU discovery | Collect actual read-only hardware/OS facts, preserve unknowns and provenance | Check evidence against target/project policy |
| PPF graph | Own node IDs, inventory relationships, process dependencies and advisory placement inputs | Validate imported graph before using it in build planning |
| Hardware AST | Parse structure and preserve byte spans | Parse/resolve/type-check source; own typed semantics |
| Registers and address spaces | Publish observed/declarative resource descriptors and ownership state | Own type/layout/effect/capability rules and safe lowering |
| MMIO/DMA | Describe evidence and protocol state; no implicit physical operation | Deny effects unless an explicit trusted platform capability exists |
| Scheduling | Estimate placement and report NUMA/cache/contention costs | Own OS/process/thread scheduler policy and platform adapters |
| Compiler backends | Supply CPU/ISA/resource evidence and test fixtures | Own instruction selection, assembler, object format, linker and compiler ABI |
| Verification | Supply graph/evidence and deterministic fixtures | Own IR verification, emulator integration, RTL/fault-report ingestion and proof admission |

## Import envelope

The proposed interchange object is defined by schemas/reaper.processor-fabric-import.v1.schema.json. It binds:

- producer identity and versioned Pytyliki schema references;
- source unit digest and offset units;
- topology/ISA evidence generation and provenance;
- PPF graph generation, ABI and stable node/edge references;
- Hardware AST construct IDs with source/body spans;
- typed resource references and dependency edges;
- explicit unresolved semantic/effect/ownership status.

The importer must treat every producer field as external data. It must validate schema, source digest, graph generation, unique IDs, reference closure, parent/edge constraints, numeric ranges and source-span bounds before adding the objects to an internal build graph. A stale topology generation or a graph referring to an earlier source digest is rejected.

The importer does not execute instructions, map addresses, schedule host threads or load arbitrary paths. The user or build configuration explicitly selects the local report file. No network fetch or implicit FFI is introduced.

## Canonical Typed IR flow

The import contract is deliberately not a substitute for Reaper IR:

1. Pytyliki emits structural construct records and graph references only.
2. Reaper resolves names and symbols against the actual source/module environment.
3. Reaper computes types, layouts, address-space relationships, effects, capabilities and ownership/borrow lifetimes.
4. Reaper creates canonical typed nodes with its own stable IDs and source-map entries.
5. The verifier checks control/data/resource dependencies, effect admission, ownership transitions, target legality and ABI constraints.
6. Only verified IR may enter HIR/MIR/LIR lowering and a selected backend.

A Pytyliki keyword such as device, memory_map, atomic_tx, probe or .section is not proof of a valid operation or a granted capability. A process-graph state of ready must not bypass Reaper verification. Imported unknown remains unknown until Reaper obtains explicit evidence.

Pytyliki source offsets are UTF-8 byte offsets. The bridge must retain the source digest and byte-length; Reaper must build its Span/SourceMap mapping from the exact checked source revision. It must never reattach a span to a different file revision or silently convert offsets under a different text encoding.

## Typed hardware resources and ownership

Reaper's type/effect layer is authoritative for the semantic use of address spaces, register banks, memory regions and DMA buffers.

- Address-space types distinguish virtual, physical, I/O-port, device-BAR and DMA-I/O virtual addresses; they are not interchangeable integers.
- Register types include width, alignment, read/write semantics, volatile behavior, reserved bits and read/clear/trigger side effects.
- Region types include checked base+length, permissions, cache policy, device identity and owner.
- DMA values carry direction, coherency, device binding, generation and an explicit ownership state.
- Borrow/lease rules prevent concurrent CPU/device mutation without a declared synchronization protocol.

A statically valid descriptor does not map memory or perform a bus transaction. MMIO reads/writes, DMA submission, cache maintenance, IOMMU updates and interrupts remain external effects behind explicit capability-checked adapters. Without the adapter, the corresponding effect is rejected at preflight/lowering.

## NUMA/cache placement and scheduling

PPF may provide a deterministic estimated placement with component scores for CPU load, affinity, NUMA locality, cache sharing, SMT sibling pressure, bandwidth and capacity. That estimate is input evidence for Reaper's processor project planner; it is not an OS placement guarantee.

Reaper Processor Control Plane remains the owner of actual CPU/thread scheduling policy and any platform callbacks. An estimate cannot call its callbacks, reserve a core or change affinity. Every placement must carry the PPF topology generation; a changed generation invalidates the estimate.

Unknown NUMA/cache topology is not interpreted as local memory or an empty cache. Tasks that require a locality guarantee must fail admission or remain pending until the required evidence is available.

## Backend ownership and pipeline

Reaper owns five independent backend contracts:

| Backend | Required input | Output evidence | Admission rule |
|---|---|---|---|
| Native assembler | Verified target-specific LIR, ISA profile, ABI | Assembly/object + relocation/source map | Every emitted instruction is legal for the target and ABI |
| Native linker | Compatible object files and linker policy | Image + symbols/relocations/map | Target, ABI, sections and ownership metadata agree |
| Emulator | Verified executable and machine model | Deterministic trace/state/fault report | Emulator semantics and model version are pinned |
| RTL | Verified microarchitecture/logic IR and timing contracts | RTL + structural/synthesis report | Clock, reset, memory and protocol assumptions are explicit |
| Formal verification | Transition system, properties and assumptions | proved / counterexample / unknown report | Unknown never counts as proof; assumptions and tool provenance are retained |

Each backend has an independent maturity record: specified, prototype, implemented or qualified. A tool descriptor is not an executable backend. A compiled host scalar C17 probe is not a native target assembler or linker. Emulator success is not hardware qualification, RTL output is not silicon, and a formal unknown is not a proof.

## Required implementation stages

1. **Pytyliki host topology collector:** read-only Windows/Linux package/die/core/thread, processor-group, NUMA and cache-sharer inventory with generation/provenance and unknown-state handling.
2. **PPF placement extension:** NUMA/cache/bandwidth contention scores and deterministic advisory planning with explicit uncertainty.
3. **Hardware resources:** validated typed descriptors and ownership state machine; Reaper compile-time/type/effect conformance cases.
4. **Reaper PPF importer:** local read-only file input, schema validation, digest/generation/source-span checks and reference closure.
5. **Canonical IR adapter:** stable Reaper IR identity, Span/SourceMap round trip, type/effect/ownership verification and malformed-input rejection.
6. **Backends:** independently deliver and qualify assembler, linker, emulator, RTL and formal verification contracts and implementations.

## Current maturity

The existing Reaper PEP v1 consumes Pytyliki host profile/benchmark report v1 and executes only its documented scalar host AOT slice. The Reaper Processor Control Plane models topology and scheduling but does not turn a PPF graph into Canonical Typed IR. No target-specific assembler, object writer, linker, processor emulator, RTL backend or formal-verification backend is claimed by these PRs.

This document is a cross-repository contract proposal. The importer and typed resource semantics remain implementation work. Keep their capability records partial until code, fixtures and CI establish conformance.
