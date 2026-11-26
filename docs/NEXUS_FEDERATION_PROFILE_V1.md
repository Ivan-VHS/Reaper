# Reaper — NEXUS Federation Profile v1

**Owner:** Reaper  
**Status:** additive integration profile  
**Compatibility:** existing language syntax, runtime, CLI, diagnostics, modules and public APIs remain unchanged.

## Role

Reaper owns the programming-language and toolchain domain: source semantics, compiler/tooling, deterministic policy evaluation, bounded workflows and explicit integration adapters. It is not renamed to `KernelCore` and is not treated as the DAK kernel.

DAK remains the OS and privileged native boundary. Reaper supplies language and policy contracts used by DAK where explicitly integrated. The current Python reference runtime, partial native C17 track and other toolchain components retain their independently documented maturity; a policy contract is not evidence of native kernel enforcement.

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
| VentuSample | `ventusample.pack.v1` and offline render metadata | Read/validate manifests as artifacts; do not load audio plugins or claim runtime coupling |
| DAK | Reaper policy contracts and bounded JSON workflows | Provide deterministic policy semantics; privileged effects remain DAK-owned |

Do not create a second message bus, duplicate report envelope or implicit service discovery runtime. Preserve opt-in semantics and permit a peer to be absent.

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
- **Stage 2.0:** any native scheduler or host bridge requires an independent design, native tests and DAK integration evidence.

## Acceptance

No public names or behavior are changed by this profile. Every claim of implementation must point to Reaper source, tests and a reproducible command. Planned service, agent, worker or scheduler concepts remain planned until executable behavior is present.
