# Reaper foundational frameworks v1

**Status:** executable reference contracts; native compiler integration remains partial.  
**Source:** `frameworks/foundation.rpr`  
**Schema:** `reaper.foundation.v1`

This first group implements five cooperating foundations rather than five competing runtimes. Each foundation owns one architectural question and publishes a small, stable Reaper-language API.

## Framework set

| ID | Framework | Responsibility | Maturity |
|---|---|---|---|
| `architecture.framework-frame.v1` | Framework frame | Structural frame, permitted relationships and project extension points | Implemented |
| `architecture.platform.v1` | Platform | OS family, target mode, ABI and platform-profile selection | Partial |
| `architecture.environment.v1` | Environment | Hosted, VM, simulated and freestanding execution profiles | Partial |
| `architecture.infrastructure.v1` | Infrastructure | Resource budgets, module graph, memory/resource ledgers and host services | Partial |
| `architecture.architecture.v1` | Architecture | Ordered language/compiler/host/backend layers and their maturity | Partial |

Maturity describes the end-to-end capability, not just the existence of a registry row. A listed contract does not imply that a target backend, kernel adapter or hardware service is complete.

## Boundaries and responsibilities

### Framework frame

The framework frame describes the repository's structural separation of concerns. Its first executable slice validates the existing project scaffold:

- `reaper/` — reference runtime and language services;
- `src/` — native C17 frontend and runtime boundaries;
- `include/reaper/` — public native contracts;
- `tests/` — language, native and integration verification;
- `docs/` — architecture and implementation contracts.

`foundation_validate_scaffold(paths)` checks that a supplied path inventory contains all five required areas. It is an inventory validator; it does not create directories or rewrite a repository.

### Platform

Platform profiles distinguish what can be used now from what remains a target:

| Profile ID | Meaning | State |
|---|---|---|
| `hosted-reference` | Existing Python reference runtime on Windows, Linux and macOS | Implemented |
| `native-c17-host` | Limited scalar AOT through a host C toolchain | Partial |
| `simulator-adapter` | Test-owned fake bus/host adapters | Partial |
| `freestanding` | Bare-metal startup, target ABI and platform services | Planned |

`foundation_validate_platform(profile_id)` rejects unknown and planned profiles. It does not probe installed toolchains or certify an ABI.

### Environment

Execution profiles separate runtime behavior from target hardware:

- `reference-runtime` — hosted compatibility runtime with explicit file/console effects and resource quotas;
- `canonical-vm` — canonical IR execution over the shared host runtime;
- `device-simulation` — fake-bus test boundary only; it does not touch a physical device;
- `freestanding` — future no-host runtime with target-defined startup, allocator, panic and I/O.

`foundation_validate_environment(profile_id)` accepts implemented and partial profiles, but rejects unknown and planned profiles.

### Infrastructure

The module publishes the runtime's known defaults and hard limits:

| Budget | Value | Meaning |
|---|---:|---|
| Module source | 2,000,000 bytes | Hard per-module source limit |
| Import depth | 64 | Hard module nesting limit |
| Execution steps | 1,000,000 | Default step quota |
| Call depth | 256 | Default call-depth quota |
| Collection items | 100,000 | Default collection bound |
| Text length | 1,000,000 characters | Default text bound |
| Heap accounting | 67,108,864 bytes | Default estimate, not an RSS/security cap |
| Open resources | 64 handles | Default resource quota |

The six-value input to `foundation_validate_budget` is ordered as:

`[steps, call_depth, collection_items, text_length, heap_bytes, open_resources]`

It requires six positive whole-number limits. The heap figure is accounting, not a process memory sandbox. Host-dispatch and device operations remain adapter- and capability-gated.

### Architecture

The canonical high-level sequence is:

`source → lexer → parser → semantic-analysis → canonical-ir → execution-engine → host-adapters → target-backend`

The layer inventory points at existing Reaper components and marks each as implemented or partial. It does not claim a full native compiler, complete type/effect checker, kernel syscall path or universal target backend.

`foundation_validate_architecture(layers)` checks exact order against the canonical sequence. This prevents an alternate pipeline from silently bypassing semantic analysis or host boundaries.

## Reaper source API

The module exports:

- `FOUNDATION_SCHEMA`, `FOUNDATION_VERSION`;
- `foundation_frameworks()`, `foundation_framework_ids()`, `foundation_find_framework(id)`;
- `foundation_validate_catalog()`;
- `foundation_scaffold_requirements()`, `foundation_scaffold_layout()`, `foundation_validate_scaffold(paths)`;
- `foundation_platform_profiles()`, `foundation_validate_platform(id)`;
- `foundation_environment_profiles()`, `foundation_validate_environment(id)`;
- `foundation_infrastructure_limits()`, `foundation_infrastructure_services()`, `foundation_validate_budget(values)`;
- `foundation_architecture_order()`, `foundation_architecture_layers()`, `foundation_validate_architecture(layers)`.

Rows are positional lists in v1 because the current .rpr grammar does not yet expose typed record declarations. Field positions are fixed by this schema; a later typed-record migration must be versioned and preserve the existing API until a compatibility transition is approved.

Example:

```reaper
import "../frameworks/foundation.rpr" as foundation

emit size(foundation["foundation_frameworks"]())
emit foundation["foundation_validate_catalog"]()
emit foundation["foundation_validate_architecture"](
    foundation["foundation_architecture_order"]()
)
```

## Verification and safety

The tests execute this module through Reaper's reference interpreter. They cover catalog shape and uniqueness, lookup, scaffold completeness, accepted/rejected platform and environment profiles, positive resource budgets and exact architecture order.

The module is pure: it does not write files, access the network, load native libraries, spawn processes, install drivers, map physical memory or change platform state. Adding a future host adapter requires a separate versioned contract, explicit capability grants, integration tests and native conformance evidence.
