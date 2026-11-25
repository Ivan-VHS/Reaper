# Reaper — NEXUS Federation Profile v1

**Owner:** Reaper  
**Status:** additive integration profile  
**Compatibility:** existing language syntax, runtime, CLI, diagnostics, modules and public APIs remain unchanged.

## Role

Reaper owns the programming-language and toolchain domain: source semantics, compiler/tooling, deterministic policy evaluation, bounded workflows and explicit integration adapters. It is not renamed to `KernelCore` and is not treated as the DuckOS kernel.

DuckOS remains the OS and privileged native boundary. Reaper supplies language and policy contracts used by DuckOS where explicitly integrated. The current Python reference runtime, partial native C17 track and other toolchain components retain their independently documented maturity; a policy contract is not evidence of native kernel enforcement.

## NEXUS vocabulary

- **Agent:** a named service/capability descriptor or policy-level component. Do not introduce a universal trait or rename public symbols without a separate compatibility proposal.
- **Nexus:** the logical federation/registry view assembled from versioned manifests. Reaper must not become a mandatory central executable gateway.
- **Worker:** a bounded task executor in a workflow. It may be a simulated policy entity until a real execution backend exists.
- **WorkerPool:** a queue/concurrency policy with explicit upper bounds, cancellation, deadlines and overload behavior.

The terms define roles, not a required Rust object model, runtime ABI or thread implementation. Reaper examples and code must use Reaper where a Reaper implementation is intended; foreign-language snippets are not substitutes for native Reaper work.

## Existing federation interfaces

Keep the current OCTA-8 topology and existing contracts authoritative:

| Peer | Existing contract | Reaper responsibility |
|---|---|---|
| OPlague | `oplage.device-snapshot.v1`, GPU telemetry snapshots | Validate schema, provenance, bounds and digest; produce a comparison/evidence report |
| Pytyliki | `pytyliki.c-abi.v1` | Call only through an explicitly trusted library path and caller-owned buffers |
| VentuSample | `ventusample.pack.v1` and offline render metadata | Reaper reference runtime validates bounded metadata, derives 22 normalized descriptors and compares manifests; it never opens WAV assets or loads DSP plugins |
| DuckOS | Reaper policy contracts and bounded JSON workflows | Provide deterministic policy semantics; privileged effects remain DuckOS-owned |

Do not create a second message bus, duplicate report envelope or implicit service discovery runtime. Preserve opt-in semantics and permit a peer to be absent.

## Implemented read-only adapters

- `ventusample_metrics(pack)` and `ventusample_compare(reference, candidate)` consume the v1 manifest contract. Comparison is deterministic, metadata-only and reports descriptor deltas plus a canonical SHA-256 report digest. V2 remains a separate contract and is not silently treated as v1.
- `oplage_gpu_normalize(snapshot)` and `oplage_gpu_load(path)` validate OPlague GPU telemetry v1 and preserve unavailable sensor values as `unknown`. The digest detects payload changes but does not authenticate a publisher or build.
- The Reaper reference runtime exposes these adapters to both tree-walk and VM execution. They remain user-space host tools; DuckOS kernel services do not import or execute peer Python modules.

## Safety and runtime boundaries

1. Resource quotas are guardrails, not a sandbox for untrusted programs.
2. Native FFI loads only a caller-selected, trusted ABI-compatible library.
3. File, process, network, clock, shell and device effects stay explicit or opt-in.
4. An unavailable or malformed peer produces a typed error and no partial privileged action.
5. Scheduling policy is not a preemptive scheduler; worker selection is not thread creation; service restart policy is not a process supervisor.
6. Reaper does not acquire driver, GPU, DMA, MMIO or kernel privileges by importing a peer contract.

## Work plan

- **Stage 0.1:** inventory language/runtime and federation interfaces; record existing API and schema owners.
- **Stage 0.2:** add compatibility fixtures for current OCTA-8 peers and schema-version failures.
- **Stage 0.3:** expose read-only federation inspection to the future Nexus Hub through validated JSON output.
- **Stage 1.0:** consider a stable Reaper service/capability descriptor only when two real consumers require it.
- **Stage 2.0:** any native scheduler or host bridge requires an independent design, native tests and DuckOS integration evidence.

## Acceptance

No public names or behavior are changed by this profile. Every claim of implementation must point to Reaper source, tests and a reproducible command. Planned service, agent, worker or scheduler concepts remain planned until executable behavior is present.
