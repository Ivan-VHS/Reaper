# Reaper — NEXUS System-Service Boundaries v1

**Owner:** Reaper  
**NEXUS role:** BuildToolchain, deterministic policy and explicit adapters  
**Status:** additive federation contract

Reaper remains the systems-programming language and toolchain repository. This profile does not rename Reaper to KernelCore, transfer kernel ownership, alter source syntax or claim that the six DAKOS services are implemented.

## Ownership

- Reaper owns grammar, language semantics, canonical IR, source diagnostics, compiler/toolchain behavior, reference runtime and the separately tracked native implementation.
- DAKOS owns privileged kernel operations, process lifecycle, service supervision, syscalls, native IPC, drivers and kernel-enforced authorization.
- BuildToolchain is the NEXUS component role for Reaper. BUILD_VANGUARD is a proposed DAKOS-owned user-space consumer of explicit build contracts, not a Reaper runtime daemon.

## Service relationships

| DAKOS service | Reaper relationship | Boundary |
|---|---|---|
| KERNEL_SENTINEL | May consume deterministic policy results and versioned integrity evidence descriptors | A policy result is not a kernel measurement source, signature verifier, scanner or enforcement hook |
| MEMORY_FORGE | May consume validated allocation-policy inputs or exported diagnostics | No privileged page inspection, allocator replacement, swap manager or VRAM access is provided |
| VECTOR_GATEWAY | May evaluate bounded policy/configuration inputs | Reaper does not implement a packet path, NIC driver, firewall hook, VPN or resolver |
| PIXEL_PIPELINE | May validate bounded resource and presentation descriptors | Reaper does not submit GPU commands, map VRAM or implement a compositor |
| DATA_ORCHESTRATOR | May evaluate deterministic scheduling, restart and capability policies | Policy selection is not context switching, process creation, a supervisor or kernel authorization |
| BUILD_VANGUARD | Supplies language/toolchain identity and documented build contracts | The service must use explicit targets and bounded execution; no implicit shell strings, network downloads or signing-key access |

## Integration invariants

1. Implement Reaper-specific policies and examples in Reaper. Do not substitute foreign-language pseudocode for a native Reaper implementation.
2. Keep the current reference runtime, native compiler track and privileged DAKOS backend as separate maturity levels.
3. Reuse existing report schemas and C ABI v1 where appropriate. A new ABI requires a separately versioned proposal and conformance tests.
4. FFI loads only a caller-selected trusted library with an explicit path and verified ABI version.
5. A missing, malformed, stale or incompatible peer produces a typed error and no partial privileged action.
6. Worker/Agent vocabulary describes roles; it does not require a universal base class, public ABI or new central daemon.
7. Do not create a second event bus, generic service framework or duplicate report envelope without two real consumers and an accepted contract.

## Required evidence before service integration

- Source and tests for each used Reaper policy contract.
- Explicit schema/version and payload-size validation at the consumer boundary.
- Negative tests for malformed, unknown, stale and unavailable providers.
- A separate native DAKOS implementation and target-backed evidence before any claim of privileged enforcement.

This profile defines ownership and integration limits. It does not add a runnable service or change Reaper language behavior.
