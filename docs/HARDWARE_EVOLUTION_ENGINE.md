# Atomic-Quantum 133 — Hardware Evolution Engine

**Project:** Reaper  
**Track:** native C17 hardware planning  
**Status:** bounded CPU/GPU work-graph planner implemented; hardware dispatch remains adapter-dependent  
**Contract:** explicit inputs, deterministic graph validation, bounded resource estimates and reviewable plans

## Purpose and interpretation

This document turns useful engineering ideas from Atomic-Quantum 133 and Psychoporter 666 into a practical hardware-development track. The first deliverable is the native C17 function reaper_hw_graph_plan: it accepts an explicit workload graph and performance/resource profile, validates the dependency DAG, and proposes CPU/GPU queue assignments.

The repository already uses Atomic-Quantum 133 as a bounded classical state-vector simulator with 133 stable function IDs and the explicit bounded_classical_simulation execution label. It is not quantum hardware control. The manifesto's fractal/self-expansion/"superposition" language is treated as an engineering metaphor: bounded candidate sets, deterministic module generation, measured variant selection, reviewed patches and explicit quotas. No physical quantum effect, infinite computation or impossible compression is claimed.

## Architecture and maturity

| Layer | Responsibility | Maturity |
|---|---|---|
| AtomForge | bounded AST/template generation, stable IDs and content fingerprints | planned |
| QuantumLab | candidate enumeration, benchmark comparison and Pareto ranking | planned |
| Hardware Graph Planner | DAG validation, CPU/GPU placement and conservative cost estimates | implemented in native C17 |
| Psychoporter Driver Analysis | inspect driver contracts, identify risks and propose patches | planned beyond current audits |
| MMIO contract | checked register descriptors and host-supplied bus callbacks | implemented C API; no physical mapping |
| Platform adapter | real device discovery, allocation, synchronization and command submission | not implemented by this planner |
| Proof/Evidence gate | tests, fuzzing, differential evidence, security review and manual approval | separate existing evolution gate; not a mathematical proof |

## Native API

- Public header: include/reaper/hw_graph.h
- Implementation: src/hw_graph.c
- Tests: tests/test_hw_graph.c

The planner accepts a CPU/GPU profile with operation and transfer throughput, queue counts and memory budgets; a bounded node array with stable IDs, operation counts, transfer bytes, memory needs, allowed backends and dependency IDs; and caller-owned output storage. Each step reports selected backend and queue, estimated start/duration/finish in nanoseconds, and whether a cross-backend dependency requires synchronization.

### Cost model

For work W and measured throughput R, duration_ns = ceil(W × 1,000,000,000 / R). GPU candidates include declared transfer cost. CPU candidates include a return-transfer estimate when consuming a GPU-produced dependency. The planner chooses the earliest feasible queue finish; CPU wins exact ties to avoid unnecessary device transfers.

This is a deterministic greedy scheduling heuristic, not a globally optimal scheduler. Estimates are only as trustworthy as the caller-supplied profile. The planner neither benchmarks hardware nor infers rates from telemetry. A profile must identify its target and measurement method outside this C API before use in a release decision.

### Bounds and memory model

- Maximum 256 graph nodes and 32 queues per backend.
- Host memory is the sum of all node reservations across the full plan.
- GPU memory is the sum of all GPU-assigned node reservations across the full plan.
- This first version does not reclaim memory between nodes. The conservative model can reject graphs that a future lifetime-aware allocator could safely reuse.
- Stable topological sorting rejects unknown IDs, duplicate dependencies, duplicate node IDs and cycles.
- The planner performs no dynamic allocation. Caller-owned nodes, dependency arrays and output storage must remain valid and non-overlapping for the call.
- The planner uses fixed-size internal arrays and returns explicit errors for invalid inputs, unsupported backend choices, resource limits and arithmetic overflow.

## Safety boundaries

1. The planner only accepts caller-supplied profiles; it does not probe hardware or launch vendor commands.
2. A plan does not grant MMIO, DMA, interrupt, firmware or driver-installation capabilities.
3. Register access remains behind include/reaper/hardware.h and a trusted bus adapter.
4. DMA ownership, IOMMU mapping, cache maintenance, fences, cancellation and device-loss recovery require separate contracts before dispatch exists.
5. Cross-backend dependencies are surfaced as synchronization requirements. A future adapter must insert correct host/device fences and account for payload bytes.
6. Driver changes must pass regression, negative, fuzz, differential, compatibility and security checks, plus maintainer review and rollback planning.
7. Malformed graphs, unavailable devices, resource overcommit and arithmetic overflow fail closed.

## Reaper and Duck OS boundary

Reaper owns the language, source/IR semantics, planner API and evidence format. Duck OS owns privileged device discovery, capability grants, physical MMIO mappings, DMA/IOMMU policy, interrupt registration, process isolation and driver lifecycle.

The first integration can consume a read-only Duck OS/OPlague hardware profile and produce an advisory plan. A profile is not authority to operate a device. A future Duck OS adapter requires a versioned DABI64 contract and hardware-in-the-loop qualification on an explicit support matrix.

## Validation

The native CTest target native-hardware-graph covers GPU-vs-CPU selection, transfer-cost tradeoffs, dependency order, cross-backend sync markers, cycles, unknown dependencies, GPU and host memory budgets, output capacity, missing GPU, independent queues, exact nanosecond rounding and overflow fallback.

The focused test executable passes locally with C17 strict warnings enabled. The full repository CTest/CI suite was not run in this environment. This is an implemented planning API, not physical GPU execution or driver management.

## Next increments

1. Version profiles and record provenance for benchmark rates.
2. Add lifetime-aware memory planning with explicit allocation/release nodes.
3. Add graph-level barrier and event contracts for CPU/GPU dependencies.
4. Add backend adapters behind explicit capabilities, beginning with a deterministic simulator.
5. Add a vendor-neutral compute API, then separately qualified Vulkan, Direct3D or Level Zero backends where platform policy permits.
6. Add hardware-in-the-loop qualification before real driver or device mutation.
7. Connect AtomForge/QuantumLab candidate generation only after stable compiler IR and deterministic fingerprints are available.
