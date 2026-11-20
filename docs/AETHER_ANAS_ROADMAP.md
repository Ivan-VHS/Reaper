# AETHER-ANAS — Reaper Integration Roadmap

**Status:** architecture proposal; documentation-only change  
**Target:** Reaper language 0.1 and later Editions  
**Normative boundary:** this document does not claim that proposed AETHER-ANAS facilities are implemented.

## 1. Purpose

AETHER-ANAS is the long-range synthesis for a language built around semantic structure, strong type guarantees, explicit effects, predictable resource use, structured concurrency and open governance. Reaper already has a small executable core. The integration strategy is therefore evolutionary: preserve the working language and make each larger capability a separately testable milestone.

The goal is not to replace Reaper with a collection of services. Reaper remains one independently installable language product with separable compiler/runtime modules.

## 2. Current implementation baseline

The following is supported by the current Reaper 0.1 implementation and its tests:

- UTF-8 source processing through a lexer, parser and tree-walking interpreter.
- Immutable `make` bindings and explicit reassignment through `vary` / `change`.
- Functions, lexical closures, recursion, lists and the `::` flow operator.
- Explicit console operations (`emit`, `say`, `ask`).
- Instruction, call-depth, collection-item and text-length limits.
- A Python 3.10+ standard-library implementation, CLI, examples and unittest suite.

These are the current baseline, not evidence that the future AETHER-ANAS runtime is complete.

## 3. Conformance map

| AETHER-ANAS principle | Reaper 0.1 state | Integration direction |
|---|---|---|
| One coherent, standalone language product | Implemented | Preserve the single package, CLI and runtime |
| Explicit data flow and composable functions | Implemented | Preserve `::` semantics and test associativity |
| Immutability as the default binding mode | Partial | Keep mutation explicit; specify collection/value semantics |
| Bounded execution and resource guardrails | Partial | Extend quotas only with pre-allocation checks and boundary tests |
| Semantic IR / content-addressed hypergraph | Not implemented | Introduce a canonical intermediate representation before considering graph storage |
| Static strong typing and type inference | Not implemented | Add a checker as a distinct compiler stage |
| ADTs and exhaustive pattern matching | Not implemented | Specify `Option` / `Result`, variants and exhaustiveness together |
| Refinement types and physical dimensions | Not implemented | Start with a small decidable subset; make solver use bounded and optional |
| Algebraic effect types and handlers | Not implemented | Model console I/O as an explicit effect before adding new capabilities |
| Arena allocation and FBIP | Not implemented | Requires a runtime/backend with an allocator under Reaper's control |
| Structured concurrency and backpressure | Not implemented | Add task scopes and bounded channels as one coherent subsystem |
| Native, GPU and distributed execution | Not implemented | Require real backends, portability tests and measured performance |
| Self-hosting compiler | Not implemented | Defer until grammar, IR and type/effect semantics are stable |

## 4. Target architecture

The proposed compiler pipeline is:

`source → tokens → syntax tree → canonical semantic IR → typed IR → execution backend`

### 4.1 Source and semantic graph

Keep `.rpr` as the readable authoring and interchange format for the initial milestones. Parse it into an immutable semantic representation with explicit source maps. Derive stable node identities from a versioned, canonical serialization of node meaning; do not derive identity from user-facing names.

The first implementation should be an in-memory IR, not a mandatory graph database. Add content-addressed caching only after canonicalization, invalidation and dependency semantics are specified. Retain source locations so diagnostics and editor actions can point back to the original program.

A future graph editor or graph-native persistence layer must preserve deterministic export, reviewable diffs, reproducible builds and a migration path for existing `.rpr` files. Do not remove ordinary source control before those properties are demonstrated.

### 4.2 Type system

Introduce a separate static-checking stage without silently changing 0.1 runtime behavior. The initial typed core should define:

1. Primitive types and function types.
2. Type inference for local bindings and functions.
3. Explicit sum/product data types, including `Option<T>` and `Result<T, E>`.
4. Exhaustive pattern matching and unreachable-branch diagnostics.
5. Explicit conversion rules; no implicit coercion between unrelated types.
6. A clearly marked dynamic boundary for gradual adoption and foreign input.

Refinement predicates should begin with decidable checks such as integer bounds and non-empty collections. An SMT solver is optional infrastructure, not a prerequisite for the first type checker. Compilation must report unknown or timed-out proofs instead of treating them as successful proofs.

### 4.3 Effects and capabilities

Preserve the principle that ordinary expressions do not gain hidden access to the host. First model existing console operations as explicit effects. Then define effect signatures, handlers, permission boundaries and deterministic failure behavior.

Filesystem, process, network, clock, FFI and hardware access must each be opt-in capabilities. Missing capabilities fail closed. An effect handler must not silently broaden the permissions of the program that invokes it.

### 4.4 Resource model

Keep the current execution-step, call-depth, collection and text quotas. Every new materializing operation must validate sizes before allocating where practical and must have tests for exact-boundary, over-limit and invalid-limit cases.

A future arena/region allocator and FBIP implementation must be backed by an execution model that controls allocation and ownership. The current Python tree-walk interpreter uses Python-managed memory; it cannot honestly promise deterministic region reclamation, zero-copy mutation or zero-cost abstractions. Such guarantees belong to a future VM/native backend and require allocation, lifetime and performance tests.

Resource budgets in function signatures may be introduced only after the semantics of accounting, composition, recursion and failure are defined.

### 4.5 Structured concurrency and streams

Do not add detached background tasks or unbounded queues. The future concurrency model should provide:

- Parent-scoped task lifetimes and cooperative cancellation of child tasks.
- Bounded channels with explicit capacity and overflow behavior.
- Backpressure that suspends or rejects producers when consumers cannot keep up.
- Deterministic scheduling hooks for tests and replayable failure scenarios.
- Explicit error propagation and cleanup when a task scope exits.

The first milestone should be a deterministic single-process scheduler. Distributed execution is a separate later backend, not an automatic consequence of the language syntax.

### 4.6 Backends and optimization

Keep the interpreter as the reference implementation while new semantics mature. A bytecode or native backend must pass the same language conformance suite. GPU and distributed targets require their own supported-feature matrices and cross-target tests.

“Zero-cost”, SIMD, cache-locality and energy-efficiency claims must be supported by generated-code inspection or reproducible benchmarks against named baselines. Do not promise a fixed editor latency such as 16 ms as a universal language guarantee; measure incremental compilation on documented hardware and representative projects.

## 5. Scientific and mathematical review gate

The physical, biological and mathematical principles in the AETHER-ANAS master document are useful sources of design metaphors and hypotheses. A metaphor is not, by itself, a proof that a language mechanism follows from a physical law.

Before any of the twelve specialized formulas becomes normative compiler or runtime behavior, record:

- A traceable publication or primary source for the equation and attribution.
- Variable definitions, units, assumptions and domain of validity.
- Dimensional analysis and limiting-case checks.
- A derivation connecting the equation to a measurable software property.
- A reproducible experiment or test that could falsify the proposed rule.

Attributions and custom indices for which the master document supplies no derivation or source remain **unverified proposals**; they must not be presented as established scientific laws. In particular, the standard Little's Law is `L = λW`. The additional factor in the supplied queue expression needs an explicit queueing-model derivation and definitions for `W` and `ρ` before it can be used.

## 6. Compatibility and Editions

Each language-breaking semantic change must be attached to an explicit language Edition. Existing 0.1 programs retain their documented behavior unless a migration is deliberately selected. New parsing, typing and effect rules should be introduced behind edition-aware tests, not through context-sensitive guesswork.

The canonical IR format, hash algorithm, normalization rules and cache schema must all carry explicit versions. Hash changes must invalidate or migrate caches safely; a hash is an identifier, not a substitute for semantic equality checks.

## 7. Governance and licensing

The current Reaper repository contains the Apache License 2.0. The AETHER-ANAS master document proposes CC0 / public-domain dedication and an anti-patent covenant. These are different licensing positions.

This roadmap does **not** replace the existing LICENSE file or change the licensing of Reaper. A license change, dual-license proposal or patent covenant requires a separate explicit decision, provenance review and legal review. Documentation must not describe the current implementation as CC0 while Apache-2.0 remains in the repository.

## 8. Implementation sequence and acceptance gates

### Stage A — Formalize the language core
- Publish a grammar and a versioned semantic specification.
- Define equality, numeric edge cases, evaluation order, errors and resource accounting.
- Add conformance fixtures for lexer, parser, interpreter and CLI.
- Acceptance: the current suite remains green and each documented rule has executable evidence.

### Stage B — Canonical semantic IR
- Define immutable IR node types, canonical serialization and source maps.
- Add stable, versioned semantic hashes and collision-safe equality checks.
- Keep `.rpr` parsing and source export intact.
- Acceptance: deterministic IR across repeated runs and supported Python versions; golden tests cover normalization and invalidation.

### Stage C — Static types and ADTs
- Add a type-checking module and typed-IR boundary.
- Implement inference, explicit ADTs, pattern matching and exhaustiveness checks.
- Specify gradual/dynamic boundaries.
- Acceptance: positive, negative and inference regression suites; no unchecked proof is treated as success.

### Stage D — Explicit effects
- Give existing console operations effect signatures and handlers.
- Specify capability grants, denial behavior and effect propagation.
- Acceptance: tests prove that programs without a capability cannot perform the corresponding operation.

### Stage E — Runtime ownership and bounded concurrency
- Prototype regions/ownership in a VM designed to control allocation.
- Add structured task scopes and bounded channels in a deterministic scheduler.
- Acceptance: lifetime, cancellation, leak, queue-capacity and backpressure tests; benchmark allocation behavior.

### Stage F — Optimizing and alternate backends
- Add bytecode first, then consider native code.
- Reuse the reference conformance suite across backends.
- Consider GPU/distributed targets only after their execution and failure semantics are specified.
- Acceptance: differential tests, reproducible benchmarks and a documented target feature matrix.

### Stage G — Self-hosting
- Stabilize the language, IR, bootstrap toolchain and reproducible build process.
- Acceptance: independently reproducible bootstrap builds and a maintained reference compiler.

No stage is complete merely because its documentation exists. Code, tests, CI evidence and updated conformance status are required.

## 9. Pull request scope

This document is a planning artifact. It does not add runtime features, alter Reaper syntax, change the license, or claim the unimplemented stages are complete. Implementation work should follow in small pull requests, each with one architectural decision, testable acceptance criteria and a rollback path.
