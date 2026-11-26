# Reaper native expansion plan — 50,000 lines per subsystem

**Status:** approved engineering target; not an implementation-completion claim  
**Baseline inspected:** `main` at `188b6782c9b672624891a14fff08d337e78092ea`  
**Target language:** Reaper (`.rpr`)

## Objective

Expand every first-party Reaper subsystem into a substantive Reaper-native implementation with a target of **50,000 qualified production source lines per subsystem**. The target is per subsystem, not a shared 50,000-line allowance for the whole repository.

The current repository is not at that scale. At the inspected baseline it contains 10 `.rpr` files with 677 physical lines and 606 non-blank lines across implementation examples and self-hosting sources. The two files under `selfhost/` account for 547 physical lines and 500 non-blank lines. Most of the current language implementation still resides in the Python compatibility runtime; the C17 compiler/runtime track is also explicitly partial. These are the facts to grow from, not a reason to relabel existing code as Reaper.

## Counting contract

A line qualifies toward a subsystem's 50,000-line target only when it is:

- executable, first-party Reaper implementation code in a maintained `.rpr` source file;
- owned by that subsystem and reachable from its declared module/API surface;
- non-duplicated, non-generated, non-placeholder implementation;
- covered by the subsystem's positive, negative, resource-limit and regression tests.

The following do **not** count toward the 50,000-line target: blank lines, comments, documentation, examples, test fixtures, generated source, registries/catalogues, JSON/YAML schemas, Python/C/C++/Rust/JavaScript code, copied code, repeated templates, no-op declarations or code that cannot be reached or verified. Reaper tests remain required and should themselves be written in Reaper where the test surface permits, but test lines are reported separately from production LOC.

The goal is capability and maintainability, not line padding. No subsystem is complete because it reaches 50,000 lines. Completion still requires its contract, implementation, tests, cross-target evidence, CI and integration review.

## Subsystem allocation

Each row has its own independent 50,000 qualified production Reaper LOC target. The resulting program-wide target is **700,000 qualified Reaper LOC across 14 subsystems**.

| ID | Subsystem | Scope that must be implemented in Reaper | Primary acceptance evidence |
|---|---|---|---|
| R01 | Lexer and source mapping | Unicode-aware identifiers; literals and escapes; comments; operator catalog; token stream; UTF-8 byte, code-point and UTF-16 coordinate projections; stable spans; malformed-input recovery | Token-by-token fixtures, Unicode/CRLF tests, stable error spans, bounded scanning |
| R02 | Parser and canonical AST | Complete grammar for declarations, functions, blocks, expressions, control flow, modules, patterns and type syntax; canonical AST constructors; incremental parse boundaries | Full grammar corpus, AST golden files, malformed syntax, parser/reference parity |
| R03 | Semantic analysis, types and effects | Name/scope resolution; fixed-width numeric types; inference and annotations; generics/constraints; Result/Option; effect and capability checking; diagnostics | Positive/negative type corpus, effect-denial tests, deterministic diagnostics, no guessed unknown types |
| R04 | Canonical IR and verification | Versioned canonical IR; HIR/MIR/LIR; Span and SourceMap; CFG and symbol tables; serialization; verifier; ABI/type/layout metadata | IR round trips, malformed-IR rejection, deterministic serialization and source mapping |
| R05 | Optimizer and analysis passes | Constant folding; propagation; dead-code elimination; control-flow simplification; inlining policy; alias/liveness analyses; target-aware lowering; bounded fixed-point pass manager | Semantic equivalence fixtures, optimization budgets, deterministic output, verifier after every pass |
| R06 | Bytecode VM and runtime | Bytecode format; verifier; interpreter/VM dispatch; calls/closures; exceptions/results; deterministic scheduling/replay; quotas; host-independent execution semantics | Reference/VM differential tests, malformed bytecode rejection, quota/fault injection and replay |
| R07 | Memory, ownership and concurrency | Stack/static/heap/region/arena models; borrow and lifetime analysis; affine/linear resources; deterministic drop/defer; atomics; synchronization and memory-order rules | Ownership negative tests, leak/use-after-release tests, race/model checks, target-specific sanitizer evidence |
| R08 | Standard library and core data model | Collections, strings/Unicode, numeric operations, ranges, iterators, formatting, algorithms, units, Result/Option helpers, time-independent core utilities | Reaper-written unit/property tests, overflow/bounds tests, complexity/resource guarantees |
| R09 | Modules, packages and builds | Import/export graph; versioned module contracts; lockfiles; dependency resolution; package manifests; incremental/reproducible builds; local cache; artifact provenance | Cycle/path/symlink rejection, lockfile reproducibility, clean-room build and compatibility matrix |
| R10 | Native compiler and architecture backends | Typed lowering; x86-64 Intel/AMD as the primary target; Elbrus retained as a separately validated backend; object emission; ELF writer, relocations, linker and loader; debug/unwind metadata | Native/reference conformance, ABI fixtures, object inspection, emulator/hardware runs and reproducible artifacts |
| R11 | ABI, FFI and system interfaces | DABI64; C ABI; typed FFI; syscall and host-call contracts; explicit effects/capabilities; safe handles; version negotiation; error and ownership boundaries | ABI layout tests, hostile-frame tests, capability denial, cross-version and cross-language conformance |
| R12 | Hardware and embedded runtime | Freestanding profiles; MMIO; register layouts; volatile/atomic semantics; DMA ownership; IRQ contexts; timers/watchdogs; cache maintenance; bus/device abstractions; simulators | Descriptor and register tests, fault injection, simulator traces, target-specific hardware/emulator qualification |
| R13 | Developer tooling and Studio | CLI/REPL; formatter; diagnostics renderer; LSP; DAP; project navigation; refactoring; build/debug orchestration; accessible native Studio integration | Protocol conformance, editor smoke tests, Unicode/UTF-16 positions, cancellation, latency and accessibility checks |
| R14 | Self-hosting and bootstrap | Reaper-written frontend, semantic/IR/compiler stages, bootstrap driver, stage manifests, deterministic rebuild, compiler provenance and recovery from a failed stage | Stage-by-stage self-hosting, clean-room rebuild, source-hash comparison and repeatable bootstrap CI |

## Dependency order

The implementation order is a dependency graph, not an invitation to build fourteen isolated code dumps:

1. R01 establishes tokens and exact source coordinates.
2. R02 consumes R01 and freezes the canonical AST.
3. R03 consumes R02 and establishes sound semantics, types and effects.
4. R04 consumes R02/R03 and freezes the canonical IR and verifier.
5. R05 consumes verified IR; R06 executes verified bytecode.
6. R07 supplies ownership and memory invariants to R03/R04/R06/R10/R12.
7. R08 builds on stable runtime and type contracts.
8. R09 resolves modules and reproducible build inputs for every compiler stage.
9. R10 and R11 establish host-native execution and stable external boundaries.
10. R12 adds explicitly privileged hardware behavior only behind target and capability checks.
11. R13 consumes the stable language-service, build and debug APIs.
12. R14 closes the bootstrap loop over the preceding implementation.

Cross-repository changes are part of each interface change: versioned contracts, compatibility fixtures, dependency updates, tests, docs and CI must be reviewed in the affected peers. No peer integration is complete solely because a manifest entry exists.

## Delivery gates

Every subsystem advances through reviewable, independently testable increments:

- **Contract:** ownership, public API, syntax/semantics, effects, errors, limits and compatibility policy are written down.
- **Core:** Reaper source implements the first complete vertical slice; no duplicated placeholder implementation.
- **Parity:** golden, negative, boundary, property and differential tests cover the declared subset.
- **Native:** relevant code runs through the intended native compiler/runtime/target, not only the Python compatibility host.
- **Integration:** dependent subsystems and affected repositories consume the versioned contract.
- **Evidence:** clean-checkout CI, target logs/artifact hashes, benchmark baselines and security review are attached to the PR.
- **Scale:** qualified production Reaper LOC is measured separately for the owning subsystem; only then can its 50,000-line target be reported.

Each delivery is a separate PR, with protected `main`, Conventional Commits, required CI and sequential review/squash merge. Do not make direct changes to `main` or report an unmerged branch as shipped.

## Expansion work delivered on the working branch

The branch now contains seven Reaper-native foundational modules:

- `selfhost/source_map.rpr` — dense codepoint-offset positions with LF/CRLF/CR handling.
- `selfhost/line_index.rpr` — sparse line starts, binary-search offset lookup, line extraction and reverse line/column lookup.
- `selfhost/span.rpr` — half-open spans with validated creation, bounds, containment, overlap, adjacency, union, intersection, shift and clamp.
- `selfhost/token_stream.rpr` — canonical four-field token record checks, EOF/ordering validation, immutable cursor operations, kind counts and value filtering.
- `selfhost/diagnostics.rpr` — structured diagnostic records, severity validation, stable ordering, count summaries and severity filters.
- `selfhost/operator_table.rpr` — precedence, associativity, binding powers and semantic categories for expression operators.
- `selfhost/ast.rpr` — canonical array-form AST nodes, recursive source-span validation, child access, node count and depth.

These modules intentionally expose a bounded initial contract. They do not claim full Unicode category handling, UTF-8 byte offsets, UTF-16 LSP positions, full statement parsing, native compiler execution or self-hosting closure. Reaper-level assertions are included and the branch's existing bootstrap test orchestration invokes each module.

The additions are the start of R01/R02 and the compiler front-end foundations; they do not satisfy any subsystem's 50,000-line target.

## Explicit exclusions and boundaries

- Python remains the current compatibility oracle until Reaper-native behavior passes differential parity. New language/compiler implementation logic is to be written in Reaper; existing host orchestration is not to be renamed and counted as Reaper.
- C17 is a current native substrate and adapter track, not proof of a complete Reaper-native compiler.
- Physical memory mapping, driver installation, firmware flashing, kernel privilege and ambient network/process/shell access are never granted by language syntax alone. They remain behind explicit versioned host/OS capabilities.
- x86-64 Intel/AMD is the primary backend path. Elbrus support is retained as an independently tested target, not silently removed or represented as complete.
- A proposed syntax feature remains proposed until grammar, semantics, implementation, diagnostics, tests and backend behavior agree.

## Reporting format

For every subsystem report: qualified Reaper production LOC; physical lines; Reaper test LOC; module/file inventory; implemented feature set; exclusions; test and CI evidence; target-runtime evidence; unresolved risks; next gate. Always state the inspected commit SHA so counts are reproducible.
