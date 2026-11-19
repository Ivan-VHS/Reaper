# REAPER — MOST Systems Architecture

**Status:** architecture proposal; implementation is staged and test-gated.  
**Target:** portable C17 core, followed by native and WebAssembly backends.  
**Compatibility:** this extends REAPER; it does not replace its current grammar or runtime.

## 1. Product definition

REAPER is an independent, flow-first systems language. MOST contributes design constraints for memory safety, deterministic resource handling, explicit effects, native interoperability and WebAssembly.

The intended product has two targets:

- **Native:** C ABI, operating-system interfaces, embedded/no-OS profiles and later x86-64, AArch64 and RISC-V code generation.
- **Web:** validated WebAssembly modules with typed browser-host interfaces.

The compiler, runtime and standard library are REAPER components. The final native toolchain should not require Python, JavaScript frameworks, Node package trees or a garbage collector. During the current C17 migration, the Python interpreter remains the semantic compatibility oracle until differential conformance is demonstrated.

## 2. Compatibility decisions

1. Preserve REAPER keywords: make, vary, change, craft, yield, emit, when, otherwise, each and loop.
2. Preserve the established flow operator ~>. MOST's |> maps conceptually to ~>; it is not silently introduced as a second spelling.
3. Do not reinterpret existing programs. New syntax requires a versioned language profile and parser tests.
4. Prefer one canonical REAPER spelling over duplicating every MOST construct.
5. Ownership, regions, effects and resource states are compile-time concepts where provable; dynamic boundaries retain runtime validation.
6. Unsafe operations are explicit and isolated; a naming convention alone does not make code safe.
7. A feature is not advertised as implemented until its backend, tests and limitations exist.

## 3. Mapping all 66 MOST principles

### I. Philosophy and independence (1–11)

| # | MOST principle | REAPER decision |
|---:|---|---|
| 1 | Anonymous context operator @ | Consider an explicit context/receiver expression only if it improves ergonomics. Named parameters remain canonical; no self/this requirement. |
| 2 | Autonomous standard library | Keep the standard library dependency-free; define reproducible bootstrap and vendor policies. |
| 3 | No implicit magic | Preserve explicit effects and conversions. Allocation, I/O, threads and host access must be visible. |
| 4 | Static typing | Add static analysis over the existing AST; dynamic values stay at explicit boundary types. |
| 5 | Canonical formatting | Specify a formatter and canonical style. Reject malformed syntax, not harmless whitespace. |
| 6 | Immutable by default | Preserve make; vary and change remain explicit mutation. |
| 7 | Deterministic execution | Define deterministic core semantics; isolate clocks, scheduling and I/O behind explicit effects. |
| 8 | Native and WASM compilation | Build backends after typed IR and semantic parity; the current interpreter is not a compiler. |
| 9 | One file, one module | Define directory-derived namespaces and visibility while retaining existing imports until migration tests pass. |
| 10 | No exceptions | Use typed result values for recoverable failures; preserve source-aware compiler and host diagnostics. |
| 11 | Self-hosting compiler | Long-term bootstrap goal. C17 comes first; self-hosting and a sub-5-MB target are not current guarantees. |

### II. Memory and safety (12–22)

| # | MOST principle | REAPER decision |
|---:|---|---|
| 12 | Region memory | Add lexical regions and region-scoped allocation to typed IR; prove escape rules before stable syntax. |
| 13 | Raw pointers | Add opaque pointers and explicit unsafe blocks; pointer arithmetic is restricted to audited unsafe operations. |
| 14 | Linear resources | Model files, sockets and handles as move-only values; require close, transfer or ownership handoff. |
| 15 | Zero-cost abstractions | Lower iterators, closures and matching to explicit loops/calls where possible; benchmark generated code. |
| 16 | Checked arithmetic | Specify checked integer operations plus explicit wrapping and saturating variants; never rely on C signed overflow. |
| 17 | No null references | Use tagged optionals and explicit matching; nullable foreign pointers are marked at FFI boundaries. |
| 18 | Layout control | Add explicit representation, alignment and packing attributes with target validation and ABI tests. |
| 19 | Safe slices | Standardize pointer-plus-length slices with bounds-checked safe indexing. |
| 20 | Stack arenas | Provide bounded arena allocation with explicit capacity and failure behavior; stack placement is target-dependent. |
| 21 | Unsafe isolation | Add an unsafe capability boundary for raw memory, assembly and privileged host operations. |
| 22 | Deterministic destruction | Implement ownership-aware cleanup in reverse acquisition order, including error-return paths. |

### III. Syntax and expressiveness (23–33)

| # | MOST principle | REAPER decision |
|---:|---|---|
| 23 | Typed declarations | Retain make/vary; add optional annotations and inference without changing declaration semantics. |
| 24 | Optional unwrapping | Add optional matching and fallback only after precedence and short-circuit rules are specified. |
| 25 | Algebraic data types | Add tagged enums and payload variants to the type system and runtime representation. |
| 26 | Exhaustive matching | Add match analysis with exhaustiveness and unreachable-branch diagnostics. |
| 27 | Traits without inheritance | Add explicit behavior contracts; avoid class inheritance and implicit dynamic dispatch. |
| 28 | Data pipelines | Keep ~> as the canonical left-to-right flow operator. |
| 29 | UTF-8 strings | Define validated UTF-8; distinguish byte indexing, scalar iteration and grapheme segmentation. |
| 30 | Named arguments | Add named arguments for longer calls while preserving positional calls and deterministic resolution. |
| 31 | No hidden globals | Keep mutable global state out of the core; pass shared state through explicit contexts. |
| 32 | Compile-time execution | Add bounded compile-time evaluation over pure expressions; no arbitrary host I/O during compilation. |
| 33 | Units and dimensions | Add compile-time dimensional types for time, bytes, length and declared units. |

### IV. Native WebAssembly and browser bridge (34–44)

| # | MOST principle | REAPER decision |
|---:|---|---|
| 34 | No Virtual DOM | Provide direct DOM or small retained-node bindings; do not promise pointers to browser internals. |
| 35 | Reactive signals | Add typed signals with explicit subscription lifetimes and deterministic teardown. |
| 36 | Declarative UI | Design optional UI syntax lowering to typed host calls; keep it out of the systems core. |
| 37 | Typed Web APIs | Provide typed WASM host bindings for DOM, Canvas, WebGL/WebGPU, audio and Fetch. Browser APIs are host capabilities, not WASM syscalls. |
| 38 | Shared client/server types | Use a versioned binary schema with validation, endianness and compatibility rules. |
| 39 | No JS framework toolchain | Produce a WASM module and minimal loader; browsers still require a host page and imports. |
| 40 | Scoped styles | Offer optional component-scoped style metadata; CSS compilation is not a runtime responsibility. |
| 41 | Async without Promise complexity | Lower async functions to explicit state machines; use browser event-loop imports or native OS adapters. |
| 42 | Routing and state | Provide optional web libraries for routing and state, not mandatory language primitives. |
| 43 | SSR and hydration | Treat SSR as a server library with a defined hydration protocol and data identity model. |
| 44 | XSS safety | Separate escaped text from trusted markup; raw HTML requires an explicit trusted type and trust boundary. |

### V. C interoperability and systems programming (45–55)

| # | MOST principle | REAPER decision |
|---:|---|---|
| 45 | C header import | Build an optional header import tool; generated bindings are checked into reproducible builds. |
| 46 | C ABI | Define stable C exports, layout rules and calling conventions; verify with compiled C fixtures. |
| 47 | SIMD | Add portable vector types to IR and lower to AVX2, NEON and WASM SIMD128 when supported. |
| 48 | Endianness in types | Provide endian wrappers and load/store functions; avoid host-endian assumptions. |
| 49 | Bit-precise integers | Support validated fixed-width integers and bitfield helpers with defined layout and overflow. |
| 50 | Race-free concurrency | Define Send-like capability traits, ownership transfer and synchronized channels before shared threads. |
| 51 | Checked inline assembly | Keep assembly in unsafe target-specific blocks with explicit register/clobber constraints and tests. |
| 52 | Cross compilation | Use target triples and reproducible toolchain manifests; SDK-dependent targets cannot be called zero-setup. |
| 53 | No-OS profile | Provide a no_std-like profile with explicit entry point, allocator and platform services. |
| 54 | Memory-mapped files | Expose OS mapping through a safe lifetime-bound view; unavailable in browser target. |
| 55 | Profiler and tracing | Add generated trace hooks and native profiling output; measure overhead and allow omission in release builds. |

### VI. Tooling, verification and evolution (56–66)

| # | MOST principle | REAPER decision |
|---:|---|---|
| 56 | Inline tests | Add test declarations or preserve the current harness; test code is excluded from production artifacts. |
| 57 | Fuzzing | Fuzz lexer, parser, type checker, serializer and runtime with reproducible corpora. |
| 58 | Executable documentation | Compile documentation examples in CI and compare expected output. |
| 59 | Stack/resource analysis | Start with conservative call-depth and stack estimates; report unknown bounds honestly. |
| 60 | No preprocessor | Use typed target conditions and compile-time branches; parse and validate all branches. |
| 61 | Reproducible builds | Normalize timestamps, paths, archive ordering and metadata; verify byte-identical outputs in CI. |
| 62 | Core cryptography | Add audited constant-time algorithms only through a separately reviewed standard-library module. |
| 63 | Content-addressed dependencies | Pin immutable source hashes and verify signatures if dependencies are introduced; no mandatory registry. |
| 64 | Generated C headers and docs | Generate headers and API docs from exported declarations; validate artifacts in CI. |
| 65 | Contracts | Add preconditions, postconditions and invariants to typed IR; distinguish static proofs from runtime checks. |
| 66 | Frozen core | Define a stable language edition and compatibility suite; freeze only after a real 1.0 process and migration policy. |

## 4. Compiler architecture

The compiler is built as explicit, testable stages:

    source
      -> lexer
      -> parser
      -> AST
      -> name and module resolution
      -> type checker
      -> ownership / region / effect analysis
      -> typed REAPER IR
      -> target lowering
          -> native object / executable
          -> WebAssembly module
      -> linker / artifact writer

### C17 migration boundary

The current native C17 branch establishes the lexer, token ownership API, CLI bring-up mode and unit tests. It is not yet a complete interpreter or compiler. The Python interpreter remains the semantic reference until the C parser, evaluator and CLI pass differential tests.

Recommended C modules, added only as implementation arrives:

    include/reaper/
      lexer.h
      parser.h
      ast.h
      type.h
      ir.h
      value.h
      region.h
      ownership.h
      effects.h
      backend.h
      wasm.h
    src/
      lexer.c
      parser.c
      ast.c
      type.c
      ir.c
      value.c
      region.c
      ownership.c
      effects.c
      backend_native.c
      backend_wasm.c

Do not create empty placeholder modules just to make the tree look complete. Each module needs a defined API, implementation and tests.

## 5. Implementation sequence and acceptance gates

### Phase 0 — Compatibility foundation
- Freeze existing REAPER 0.x syntax and runtime behavior in fixtures.
- Finish C17 lexer and parser migration without changing program meaning.
- Add differential tests against the Python reference.
- Document which MOST requirements remain design-only.

**Gate:** existing examples and tests produce equivalent results or diagnostics in C and Python.

### Phase 1 — Static semantic core
- Add type representation, inference and diagnostics.
- Add tagged enums, optionals and exhaustive matching.
- Add checked integer semantics and explicit result values.
- Define typed IR and canonical formatter.

**Gate:** negative type tests, exhaustiveness tests, overflow tests and stable IR snapshots pass.

### Phase 2 — Memory and effects
- Add region scopes, slices, move-only resources and deterministic cleanup.
- Add unsafe boundaries, pointer provenance rules and explicit FFI types.
- Add effect declarations for filesystem, network, clock, process and host access.
- Add Send-like transfer checks and safe synchronization.

**Gate:** compile-fail tests reject use-after-move, invalid region escape and unsupported data races.

### Phase 3 — Native systems target
- Add C ABI import/export and layout conformance.
- Add native object generation and target-specific linking.
- Add no-OS profile, allocator interface and platform adapters.
- Add SIMD and endian-safe primitives.

**Gate:** C interoperability fixtures, cross-target tests and embedded smoke tests pass on declared targets.

### Phase 4 — WebAssembly bridge
- Add a WASM code-generation backend and minimal loader.
- Define typed imports for browser capabilities.
- Add binary serialization, async state-machine lowering and resource teardown.
- Add optional UI, signals, routing and SSR libraries.

**Gate:** browser integration tests pass without a JavaScript application framework; WASM imports and memory limits are documented.

### Phase 5 — Toolchain maturity
- Add formatter, documentation tests, fuzzing and profiling.
- Add reproducible artifact verification and dependency hash validation.
- Add compile-time evaluation and contract checking.
- Begin self-hosting only after native compiler stability.

**Gate:** reproducible builds, fuzzing corpus, conformance suite and release policy are maintained in CI.

## 6. Security and correctness rules

- C implementation must not rely on undefined behavior for language semantics.
- Every allocation has a documented owner and failure path.
- Foreign pointers, browser imports and serialized data are untrusted until validated.
- A region cannot be destroyed while a live safe reference points into it.
- A move-only resource cannot be copied or silently discarded.
- Async cancellation must run cleanup exactly once.
- WASM sandboxing does not replace validation of host imports.
- Cryptographic code requires independent review and test vectors.
- Compile-time evaluation has deterministic resource budgets.
- Static analysis reports uncertainty explicitly; it must not claim a proof where only a heuristic exists.

## 7. What is not implemented or guaranteed yet

The following remain future work until code and tests demonstrate them:

- a complete C17 REAPER compiler or interpreter;
- native x86-64, ARM64 or RISC-V machine-code generation;
- a working WASM backend or browser UI runtime;
- borrow checking, region escape proofs or complete linear-resource analysis;
- automatic C-header ingestion;
- a self-hosted compiler or sub-5-MB distribution;
- universal cross-compilation without target SDKs;
- formally verified cryptography or constant-time behavior on every target;
- guaranteed byte-identical artifacts across every toolchain and platform.

## 8. Architectural outcome

REAPER adopts the strongest MOST ideas while retaining its language identity and implementation history:

- one source language with explicit effects and predictable semantics;
- one typed intermediate representation shared by native and WASM backends;
- one ownership and region model rather than separate memory rules per target;
- one standard-library contract with platform-specific adapters;
- one conformance suite gating every backend and release.

**Governing principle:** a capability belongs to REAPER only when its semantics are specified, its implementation exists and its behavior is tested.
