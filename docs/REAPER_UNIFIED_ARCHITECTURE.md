# REAPER / MOST — Unified Architecture and Delivery Contract

**Purpose:** consolidate the decisions and implementation tracks from the REAPER, MOST, C migration, Reapers architecture, AETHER-ANAS and feature-registry discussions into one source of truth.

**Implementation language:** portable C17. C23 is a later, optional language-standard upgrade after toolchain support and conformance are established.

**Truth rule:** a design proposal is not an implementation. A capability is marked implemented only when source code, public contract, tests and a passing CI/conformance result exist.

## 1. Product identity

REAPER is an independent, flow-first systems programming language. It keeps its own syntax, identity, small core and explicit data-flow model. It is not a renamed C, Rust, Swift, Python or JavaScript.

The original surface constructs remain part of the compatibility contract:

- `make`: immutable binding by default.
- `vary`: explicitly mutable binding.
- `change`: explicit reassignment.
- `craft` / `yield`: function declaration and result production.
- `when` / `otherwise`, `each`, `loop while`: control flow.
- `~>`: left-to-right flow composition.
- Explicit conversions and explicit host effects.

The native C17 implementation is the destination implementation. The Python 0.1 interpreter is a temporary compatibility oracle only; it must not be required to build, test, install or run the final native release. Remove it only after differential parity over the complete language and CLI contract.

## 2. MOST / Мост relationship

MOST is the Russian-language semantic frontend and systems/web language track associated with REAPER. It is not a second runtime, memory model or independent backend.

Responsibilities:

- REAPER frontend: canonical REAPER syntax and AST.
- MOST frontend: Russian source vocabulary, intent AST, scoped domain dictionaries and ambiguity diagnostics.
- Shared semantic core: name resolution, types, effects, ownership and contracts.
- Shared Canonical IR: both frontends lower to equivalent typed IR.
- Backends: native targets and WASM consume the same verified IR.

Synonyms and morphology may resolve a source name, but may never change type, overload choice, effects or execution semantics. Ambiguous intent is a compile error with source mapping. No probabilistic service may silently choose program meaning.

## 3. Canonical compilation pipeline

```text
REAPER source ─┐
               ├─> lexer ─> parser/AST ─> name + intent resolution
MOST source ───┘                              │
                                             v
                         typed AST / semantic analysis
                                             │
                         ownership + region + effect checks
                                             │
                                             v
                                Canonical Semantic IR
                                             │
                           verifier ─> optimizer passes
                                  ┌──────────┴──────────┐
                                  v                     v
                            Native backend          WASM backend
                                  │                     │
                                  v                     v
                             C ABI / OS          WASI / Browser host
```

Frontend-specific syntax must not leak into the IR. IR is deterministic, source-mapped, backend-neutral and structurally verifiable. Optimizers may only preserve observable semantics.

## 4. Language and safety invariants

1. Static types; immutable bindings by default; explicit mutation.
2. No tracing garbage collector. Ownership, borrowing, regions and linear resources are checked statically before native code generation.
3. Shared borrows may alias; mutable borrows are exclusive.
4. Resource handles are consumed, transferred or deterministically closed exactly once.
5. Unsafe pointer arithmetic, assembly, raw memory and privileged hardware access require explicit unsafe scopes and capabilities.
6. Bounds, integer overflow, division by zero and invalid conversions have specified semantics; no undefined behavior is an accepted language feature.
7. Arithmetic is checked by default; wrapping and saturating operations remain distinct.
8. Effects such as I/O, allocation, mutation, clock, randomness, network, process, shell and hardware access are explicit and capability-gated.
9. Cancellation, budgets, quotas and timeout outcomes are explicit values/errors.
10. No implicit thread creation, ambient authority, hidden allocation or background work.
11. Every allocation has an owner and every public API documents lifetime and failure behavior.
12. Resource quotas are guardrails, not a security sandbox.

## 5. Reapers-derived systems architecture

The Reapers / Mass Effect-inspired concepts are engineering metaphors, not lore-dependent runtime behavior:

| Concept | Engineering subsystem | Required invariant |
|---|---|---|
| EpochArena | Region and arena allocator | Bounded lifetime, explicit escape rules |
| Effect Context | Effect/capability context | No ambient authority |
| Typed Local Relays | Typed channels and local message passing | Typed payloads, bounded queues |
| FIFO Actors | Actor scheduler | Explicit ordering, cancellation and backpressure |
| Hot Node Profiler | Runtime/compiler profiler | Measured overhead and source correlation |
| SHA-256 Snapshots | Content-addressed build/cache snapshots | Canonical serialization and hash verification |
| Vanguard Monitoring | Health and resource monitoring | Observable limits and deterministic failure states |
| AETHER-ANAS | Dependency graph / system orchestration | Explicit DAG, cycle diagnostics and bounded scheduling |

JIT, distributed transport, supervisor trees, GPU execution, lock-free structures, persistent storage and hardware control remain separate projects until each has a concrete safety model and target-specific acceptance tests.

## 6. Unified feature registries

The existing registries are preserved and reconciled, not discarded:

- 66 MOST foundation rules: language constitution and semantic invariants.
- 147-feature registry: first extended capability catalogue.
- 813-feature architecture map: broader subsystem and platform roadmap.
- Additional cognitive/text/data proposals: optional tooling or services, never implicit compiler semantics.

Number ranges are planning identifiers, not promises of completed functions. Before implementation, each feature must have:

- stable ID and canonical name;
- owning subsystem and dependencies;
- public API/syntax and semantic contract;
- input/output types and error model;
- effect/capability requirements;
- target availability and fallback behavior;
- unit, negative, integration and conformance tests;
- performance/resource budget where relevant;
- status: proposed, specified, implemented, verified, deprecated.

Duplicate or overlapping proposals are merged under one canonical ID while preserving aliases and provenance. New keywords are added only when a library API or compiler attribute cannot express the capability cleanly.

## 7. Delivery architecture

| Phase | Deliverable | Exit gate |
|---|---|---|
| N0 | C17 build, lexer, diagnostics, CLI | Native build and lexer tests |
| N1 | Parser, owned AST, complete declarations/blocks | Grammar, recovery, fuzz and source-span tests |
| N2 | Typed AST, symbols, MOST intent resolver | Type/ambiguity and equivalent-frontend tests |
| N3 | Canonical IR lowering and verifier | Typed lowering and malformed-IR rejection |
| N4 | Optimizer pipeline | Semantic equivalence, overflow and determinism tests |
| N5 | Ownership, borrow, regions, drop and effects | Negative safety tests and CFG analysis |
| N6 | Native backend and runtime | ABI fixtures and differential behavior suite |
| N7 | WASM/WASI/browser host | Capability boundary and browser conformance |
| N8 | Standard library, package/build system, tooling | Reproducible builds, fuzzing and docs tests |
| N9 | Self-hosting and compatibility freeze | Bootstrap and reproducibility proof |

The existing 147 and 813 maps are mapped onto these phases and subsystem owners; they do not create parallel delivery tracks.

## 8. Current native implementation boundary

On `feat/reaper-most-parser-m1`, the repository contains:

- C17 build, native lexer and token ownership API;
- expression Pratt parser and owned AST;
- small canonical IR model and structural verifier;
- checked signed-i64 constant-folding pass.

The current parser handles expressions, not complete modules, declarations or blocks. The current IR supports only integer constants, signed-i64 addition and return. This is not yet a complete type checker, native compiler, interpreter or WASM runtime.

The next implementation increment connects the owned AST to the verified IR for the deliberately small integer-expression subset. Unsupported syntax must fail explicitly until its semantics are implemented.

## 9. Build and verification contract

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

CI must run native C17 builds and tests on supported compilers. Python differential tests remain temporary compatibility gates, not native build dependencies. A green local test is not a substitute for CI evidence.

## 10. Related source documents

- `docs/MOST_LANGUAGE_SPEC.md`: foundational language semantics and 66-rule contract.
- `docs/MOST_147_FEATURE_REGISTRY.md`: first extended feature registry.
- `docs/REAPER_813_FEATURE_ARCHITECTURE.md`: expanded subsystem roadmap.
- `docs/MOST_IMPLEMENTATION_STATUS.md`: executable implementation ledger.
- `docs/C_MIGRATION.md`: Python-to-C17 parity and migration gate.
- `docs/REAPER_PARSER_M1.md`: parser milestone contract.

This document is the integration map. Detailed specifications remain in their owning documents; contradictory status statements must be reconciled in the implementation ledger before a feature is called complete.
