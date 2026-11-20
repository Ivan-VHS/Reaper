# Reaper / MOST — 48-point engineering architecture and acceptance roadmap

**Status:** integrated architecture contract and traceability map.  
**Scope:** REAPER language, MOST (Мост) frontend, shared semantic core, Canonical IR, runtimes, native/WASM backends and developer tooling.  
**Truth rule:** this document maps requirements to the existing architecture. It does not claim that all 48 capabilities are implemented.

## 1. Integration decision

The 48 engineering proposals are adopted as a cross-cutting quality and delivery framework for REAPER/MOST. They do not create a second language, another runtime, a parallel compiler pipeline or a new feature-count registry.

The existing division of responsibility remains authoritative:

- **REAPER frontend:** canonical REAPER syntax, lexer, parser and source AST.
- **MOST frontend:** Russian-language syntax vocabulary, morphology/domain resolution, intent diagnostics and source mapping. Resolution must be deterministic; ambiguous meaning is an error, never a guess.
- **Shared semantic core:** name resolution, types, contracts, effects, ownership, regions and resource validation.
- **Canonical IR:** immutable, typed, source-mapped and independently verified representation shared by both frontends.
- **Execution targets:** the Python reference interpreter remains the compatibility oracle for its implemented language subset; the native C17 implementation is the destination compiler/runtime track; native and WASM backends must consume the same verified semantics.
- **Tooling:** CLI, REPL, formatter, linter/checker, tests, debugger, language server and build tooling are clients of the language contracts, not alternate sources of semantics.

The current canonical REAPER flow operator is `::`. It passes the left-hand value as the first argument to the next operation and associates left to right. Architecture references using `~>` are legacy wording and must not define a second operator or an undocumented alias.

## 2. The 48-point crosswalk

Status describes end-to-end capability across the intended REAPER/MOST architecture, not whether a token, name or proposal appears in a document.

| # | Engineering requirement | REAPER / MOST integration and current boundary | Status | Acceptance gate |
|---:|---|---|---|---|
| 1 | One unambiguous canonical grammar | REAPER's reference grammar and precedence are documented; native C currently has an expression-parser slice, not the full grammar. MOST shares the semantic core and must not guess morphology. | Partial | Grammar specification, parser agreement, ambiguity tests, source spans and fuzz corpus. |
| 2 | Expressions return values | Preserve expression-oriented declarations, calls and flow composition; add value-producing control/block forms only through a versioned grammar decision. | Planned | Every branch yields a compatible value; unreachable/missing branches are diagnosed; evaluation order is tested. |
| 3 | Explicit immutable and mutable state | REAPER reference runtime has `make`, `vary` and `change`; MOST specifies immutable-by-default bindings and explicit mutation. | Partial | Equivalent frontend behavior, reassignment diagnostics and mutation/alias tests in shared conformance vectors. |
| 4 | Exhaustive pattern matching | MOST specifies enums and compile-time exhaustiveness; full pattern grammar and type checking are not yet implemented. | Specified | Nested pattern tests, unreachable-arm diagnostics and exhaustive/non-exhaustive enum fixtures. |
| 5 | Left-to-right data pipelines | REAPER's `::` operator and collection functions are implemented in the reference runtime. Keep one operator and one lowering rule across frontends. | Implemented | Golden AST/IR vectors prove argument insertion, order, associativity and error propagation. |
| 6 | Concise closures and local functions | Functions, lexical closures and higher-order collection operations exist in the reference runtime; native parity and a complete local-function grammar remain separate gates. | Partial | Capture-by-value/reference rules are explicit; lifetime, recursion and mutation tests pass. |
| 7 | Interpolation and robust string literals | Escaped UTF-8 strings and string utilities exist; interpolation, raw and multiline literal forms require a deliberate grammar and escaping policy. | Partial | Lexer/parser round-trip fixtures, Unicode tests and injection/escaping boundary tests. |
| 8 | Canonical formatter | Canonical indentation is specified for MOST, but a repository-wide authoritative formatter is not yet an established feature. | Planned | Idempotent formatting, parse-preservation, stable diffs and formatter/parser agreement in CI. |
| 9 | Explicit optional values | REAPER 0.1 has a `nothing` value; MOST specifies tagged optional/result types. Static null-safety is not yet end-to-end. | Partial | No implicit nullable dereference; exhaustive absence handling and stable ABI/layout tests. |
| 10 | Algebraic data types | Structs, tuples, payload enums and option/result types are part of the MOST type contract; compiler enforcement remains future work. | Specified | Type-checking fixtures prove valid construction, invalid-state rejection and exhaustive matching. |
| 11 | Constrained generics | Traits and generic/monomorphized compilation belong to the typed compiler design; dynamic `Any` fallback is not an acceptable substitute. | Specified | Constraint solving, monomorphization determinism, code-size bounds and generic ABI tests. |
| 12 | Local inference, explicit public contracts | Static type inference and typed public signatures belong to the semantic checker, which is not yet complete. | Planned | Inferred/local and annotated/public signatures produce equivalent typed IR; error messages identify failed constraints. |
| 13 | Refinements and contracts | MOST reserves contract concepts such as `requires` and `ensures`; a contract checker and proof model are not yet implemented. | Specified | Preconditions, postconditions and invariants are checked at defined boundaries with bounded evaluation. |
| 14 | Checked, wrapping and saturating arithmetic | MOST defines checked-by-default arithmetic plus distinct wrapping/saturating operators. Native C17 constant folding rejects signed-i64 overflow; this is not full runtime parity. | Partial | Identical overflow, division and conversion semantics across interpreter, IR and each backend. |
| 15 | Nominal/newtype domain values | Opaque/newtype and unit-safe values fit the typed semantic core; they are not yet a complete compiler feature. | Specified | No implicit interchange of unrelated domain types; representation and FFI layout are tested. |
| 16 | Explicit effects and pure computation | REAPER exposes host effects explicitly and gates native FFI; MOST specifies effect declarations/capabilities. Static transitive effect checking remains open. | Partial | Effect rows/capabilities are verified transitively; denied effects fail before execution. |
| 17 | Deterministic resource cleanup | The Python reference runtime provides owned file handles, scoped `with_file`, cleanup and LIFO regions. Native deterministic drop/linear ownership is not complete. | Partial | All exit paths close/transfer each resource once; failure, cancellation and early-return tests pass. |
| 18 | Expected errors versus fatal faults | Source-aware language/runtime failures and structured CLI results exist; a complete typed error taxonomy across native compilation is not finished. | Partial | Stable error classes distinguish user errors, resource failures and internal compiler faults. |
| 19 | Error propagation operator | Do not overload `??` (optional fallback) or the flow operator. A dedicated propagation form requires a versioned grammar decision and typed Result semantics. | Planned | Propagation preserves error type/cause and source context without swallowing failures. |
| 20 | Structured error context | REAPER has source-aware diagnostics, JSON CLI output and an execution audit trail; a single structured error/cause schema is still needed. | Partial | Stable machine-readable codes, source spans, causes and sanitized context are tested. |
| 21 | Exhaustive error handling | Must-use results and compile-time error-set coverage depend on the future static semantic checker. | Planned | Ignored fallible results are diagnosed; API boundaries handle every declared failure case. |
| 22 | Cancellation, deadlines and retries | Resource budgets and cooperative stopping are established foundations; structured cancellation, deadlines and idempotent retry policies remain specified/runtime-roadmap work. | Specified | Parent-child cancellation, timeout cleanup, retry caps and idempotency are tested deterministically. |
| 23 | Transparent memory and value costs | Reference heap accounting and owned native AST structures exist, but Python's physical allocator is still authoritative and the final native memory model is incomplete. | Partial | Allocation, copy/move, lifetime and stack/heap costs are documented and measured per target. |
| 24 | Multiple explicit memory strategies | LIFO regions and tracked heap accounting exist in the Python reference; native ownership/borrowing, arenas and allocators need static enforcement and backend parity. | Partial | Region escape, borrow exclusivity, allocation failure and allocator-boundary tests. |
| 25 | Structured concurrency | The current reference interpreter is sequential. Tasks, coroutines and scheduler semantics are not implemented. | Planned | Parent/child lifetime, cancellation, bounded queues, backpressure and deterministic shutdown tests. |
| 26 | SIMD and data parallelism | CPU/MCU/ISA and toolchain capability catalogues exist; catalogue discovery is not SIMD lowering or parallel execution. | Specified | Scalar-equivalence tests, target feature detection, fallback behavior and race/safety tests. |
| 27 | Explicit data layout and alignment | C ABI, target profiles and layout requirements are specified; complete native layout/code-generation guarantees remain future work. | Specified | Size/alignment/offset/endian fixtures for every supported ABI and serialized representation. |
| 28 | Safe, predictable FFI | The Python reference has opt-in typed C ABI/Pytyliki adapters. It executes trusted native code in-process and is not a sandbox; native C parity is incomplete. | Partial | ABI version, calling convention, ownership, error mapping and negative compatibility tests. |
| 29 | Profiling, benchmarks and allocation metrics | CLI `--profile`, step counts and reference heap statistics exist; a cross-backend profiler and repeatable benchmark suite are incomplete. | Partial | Workload provenance, warm-up, repeated runs, allocation counts and no timing claims without measurements. |
| 30 | Bounded compile-time computation | MOST recognizes the `comptime` design direction; deterministic compile-time evaluation/macros are not implemented by token recognition alone. | Specified | Fuel, recursion and memory limits; deterministic outputs; no ambient I/O or code execution. |
| 31 | Modules, namespaces and dependency graphs | Python `.rpr` imports/exports, module isolation, caching and cycle diagnostics are implemented; native/MOST module parity remains open. | Partial | Identical visibility, cycle and dependency diagnostics; incremental rebuild invalidation tests. |
| 32 | Package management and reproducible dependencies | Python packaging through `pyproject.toml` exists; a first-class Reaper package/lock/resolution system does not. | Partial | Content/version pinning, provenance, integrity checks and offline reproducible resolution. |
| 33 | Compatibility and migration tooling | Compatibility rules and versioned evolution are documented; an automatic source migrator is not implemented. | Planned | Version-to-version fixtures, deterministic `fix` output and migration round-trip tests. |
| 34 | Documentation and executable examples | Language/runtime documentation and examples exist; uniform documentation comments and doctest enforcement are incomplete. | Partial | Every published example is checked/run in CI; API docs are generated from canonical declarations. |
| 35 | Test runner and generative testing | Python `unittest` and native CMake/CTest suites exist; a complete language-level test syntax/runner and property-based pipeline are not complete. | Partial | Unit, integration, table-driven, property and fuzz tests run under shared resource limits. |
| 36 | Focused standard library | Collections, UTF-8 strings, metrics, modules, files and selected FFI helpers exist in the reference runtime; coverage is not yet a complete cross-target library. | Partial | Each public operation has typed inputs, complexity, limits, effects and errors; native parity is recorded. |
| 37 | Configuration and data formats | JSON CLI output and explicit module metadata exist; a unified configuration/schema/localization contract remains incomplete. | Partial | Versioned schemas, bounded parsers, validation diagnostics and locale-independent core semantics. |
| 38 | Actionable diagnostics | Lexer/parser source locations and runtime diagnostics exist; native recovery, suggestions and cross-stage diagnostic parity remain open. | Partial | Primary span, cause, note/help, stable code and regression fixture for every diagnostic class. |
| 39 | Fast incremental feedback | REPL, check/lint CLI and native build/test targets exist; a complete incremental compiler/watch service is not established. | Partial | Measured edit-check latency, correct invalidation and no stale semantic results. |
| 40 | LSP, debugger and observability hooks | Reaper Studio provides statement-level debugging; a standards-complete LSP and native async debugger are not implemented. | Partial | Completion, hover, navigation, rename, breakpoints and source-mapped stack frames share compiler diagnostics. |
| 41 | Static linting and analysis | `--lint` currently aliases validation/checking; this is not a complete static analyzer or type checker. | Partial | Rules are versioned, deterministic, configurable and covered by positive/negative fixtures. |
| 42 | Reproducible builds | CI, pinned language baselines and deterministic IR requirements are established; bit-for-bit native artifact reproducibility still needs proof. | Specified | Clean-room builds with pinned inputs produce verified identical artifacts and provenance. |
| 43 | Logs, metrics and tracing | Structured JSON output, execution profile and hash-chained audit records exist; vendor-neutral runtime tracing is incomplete. | Partial | Explicit opt-in events, bounded buffers, privacy-safe defaults and trace-correlation tests. |
| 44 | Readability and onboarding | Small REAPER surface syntax, reference documentation and runnable examples form the current baseline; diagnostics and formatter work strengthen it. | Partial | New-user examples, consistent naming and code-review readability checks. |
| 45 | Safe-by-default unsafe boundaries | MOST specifies explicit raw/unsafe operations and capability boundaries; a complete compiler-enforced unsafe checker is not implemented. | Specified | Unsafe scopes are minimal and auditable; safe IR rejects unchecked pointer/effect operations. |
| 46 | Cross-platform and multi-architecture portability | Python is portable; architecture/toolchain matrices and C17 bring-up exist. Native code generation for every listed target is not implied. | Partial | Target-specific ABI fixtures, feature-gated fallbacks and OS-independent semantic conformance. |
| 47 | GPU and accelerator readiness | Architecture/toolchain catalogues describe possible targets; no general GPU compiler/runtime capability is claimed. | Specified | Explicit accelerator ABI, memory transfer, synchronization and fallback contracts plus real device tests. |
| 48 | Small, reversible evolution | Versioning, implementation-status ledgers and a C17 evolution evidence gate support controlled change; full semantic migration automation remains future work. | Partial | RFC/design review, compatibility suite, rollback path and passing CI before promotion to stable behavior. |

## 3. Priority and implementation order

The 48 requirements are not 48 simultaneous coding tasks. Delivery follows the existing REAPER/MOST milestones and keeps the reference/native boundary honest.

### P0 — Protect the implemented core

Keep the canonical grammar and `::` flow semantics stable; preserve explicit mutation, string and numeric rules, source-aware diagnostics, bounded execution, deterministic cleanup, module behavior, opt-in FFI and reproducible tests. Close mismatches between the Python reference and the current C17 slice before expanding the public language surface.

**Exit evidence:** shared golden syntax/AST/IR vectors, normal and failure-path tests, quota tests, updated references and green Python plus CTest suites.

### P1 — Finish the language and semantic core

Complete declarations and blocks in the native parser, source spans and recovery; then implement name resolution, typed AST, Option/Result, ADTs, exhaustive match, generics, inference, refinements/contracts, effect checking and typed Canonical IR.

**Exit evidence:** type-checking and negative fixtures, cross-frontend semantic equivalence, IR verifier coverage and deterministic diagnostics.

### P2 — Establish safe native execution

Implement ownership/borrowing, regions, linear resources, deterministic drop, checked arithmetic and FFI/layout contracts before native code generation. Add structured concurrency, cancellation, SIMD and accelerator work only as separately gated capabilities with bounded resource models.

**Exit evidence:** ownership/region negative tests, ABI/layout fixtures, sanitizers, backend differential tests, and resource/cancellation tests.

### P3 — Complete the developer and package ecosystem

Deliver formatter, static analysis, LSP, migration tooling, language-level tests, documentation tests, package/lock resolution, configuration schemas, profiling and reproducible artifact builds.

**Exit evidence:** formatter idempotence, editor protocol tests, migration corpus, offline package builds, generated-doc checks and reproducibility comparison.

## 4. Mandatory acceptance contract for every change

Every proposed language or runtime improvement must answer all of the following before implementation:

1. **Need:** which concrete user or compiler problem does it solve, and why is an existing library function, attribute or tool insufficient?
2. **Semantics:** syntax, precedence, evaluation order, types, ownership, effects, errors and compatibility impact.
3. **Composition:** interaction with `::`, functions, modules, async/resource lifetimes, FFI and both frontends.
4. **Cost:** compile-time work, runtime overhead, allocation, code size and target limitations.
5. **Safety:** resource limits, capability requirements, failure cleanup and unsafe boundary.
6. **Evidence:** reference tests, native tests where implemented, cross-backend vectors, negative cases and CI result.
7. **Evolution:** versioning, migration note, rollback path and documentation update.

A new keyword is accepted only when the construct cannot be expressed clearly through the existing grammar, standard library or compiler attributes. Operator overloading, implicit conversions, ambient effects, hidden allocations, global mutable state and implicit task spawning are rejected unless a separate proposal proves their semantics and safety.

## 5. Conformance labels

Use these labels consistently in this roadmap and related registries:

- **Implemented:** executable behavior exists in the stated target, is documented and is covered by tests/CI.
- **Partial:** a bounded subset exists; the missing scope and target are stated.
- **Specified:** semantics or architecture are documented, but executable implementation is absent.
- **Planned:** accepted direction with implementation work not yet started.
- **Not applicable:** outside the product boundary unless a deliberate architecture decision changes that boundary.

A feature must be reported per target when the Python reference, native C17 implementation, MOST frontend and WASM backend differ. A token, catalogue entry, architecture paragraph, toolchain discovery result or sample snippet is not implementation evidence.

## 6. Related source of truth

- [Unified REAPER/MOST architecture](REAPER_UNIFIED_ARCHITECTURE.md)
- [Unified engineering standard](UNIFIED_ENGINEERING_STANDARD.md)
- [MOST language specification](MOST_LANGUAGE_SPEC.md)
- [MOST implementation status](MOST_IMPLEMENTATION_STATUS.md)
- [Runtime platform contract](RUNTIME_PLATFORM.md)
- [Native parser M1 contract](REAPER_PARSER_M1.md)
- [66-rule architecture contract](ARCHITECTURE_66.md)
- [20-system engineering programme](20_SYSTEM_ENHANCEMENTS.md)
- [666-rule conformance profile](CONSTITUTION_666_PROFILE.md)

This roadmap is a crosswalk across those contracts. If implementation evidence changes, update the owning implementation ledger and this status map together; do not create a parallel claim of completion.
