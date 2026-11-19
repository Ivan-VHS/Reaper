# MOST — language architecture and implementation contract

**Status:** language design integrated into the native REAPER development line; lexical foundation only. This document is a specification and staged acceptance contract, not a claim that all 66 capabilities exist.

MOST is the systems-and-web language track of REAPER. It targets deterministic native code and WebAssembly from one statically typed source language. The C17 implementation is the bootstrap host; it is not the language's permanent runtime requirement.

## Design invariants

1. No subject-oriented receiver keywords. `@` denotes the current lexical receiver/context.
2. No implicit allocation, conversion, thread creation, exception unwinding, or ambient global state.
3. Static types, immutable bindings by default, explicit mutation, explicit effects.
4. No tracing garbage collector. Region/arena allocation and linear resource ownership are checked statically.
5. A single source model lowers to verified typed IR, then to native or WASM backends.
6. The Python interpreter remains a compatibility oracle until the native implementation passes differential conformance; it is not a MOST backend.
7. Every capability has an implementation state and executable acceptance tests. Roadmap text never counts as implementation.

## Canonical surface syntax

The language uses canonical four-space indentation, braces for blocks, UTF-8 identifiers, and a formatter/parser agreement. The first native lexer accepts the token vocabulary; grammar and semantic enforcement are subsequent gates.

```most
module counter

struct State {
    value: signal<i32> = 0
}

fn increment(@: ~State, step: i32) -> i32 {
    @.value = @.value +| step
}

test "saturating counter" {
    let mut count: i32 = i32.MAX
    count = count +| 10
    assert(count == i32.MAX)
}
```

The lexer recognizes the initial MOST keyword family (`module`, `import`, `fn`, `struct`, `enum`, `trait`, `impl`, `region`, `raw`, `arena`, `signal`, `async`, `await`, `match`, `test`, `comptime`, `requires`, `ensures`, and related control/type words) and multi-character operators including `|>`, `??`, `+%`, `+|`, `->`, and `:=`. Token recognition does not imply parser or runtime support.

## Compiler pipeline

`UTF-8 source → tokens → CST/AST → name resolution → type/effect checking → ownership & region analysis → typed MOST IR → verification/optimization → native or WASM backend`.

The IR must be immutable, source-mapped, deterministic and independently verifiable. Frontends must not emit machine code directly. Backend selection must not change source semantics.

## Memory and safety model

- **Regions:** lexical region scopes own bulk allocations; escape analysis prevents references outliving a region.
- **Borrows:** shared immutable borrows may alias; mutable borrows are exclusive. The compiler rejects overlapping mutable access.
- **Linear resources:** file/socket/lock handles are consumed by close, transfer, or a verified scope destructor exactly once.
- **Raw operations:** pointer arithmetic, inline assembly and hardware access require an explicit unsafe function/block and are excluded from safe proofs.
- **Slices:** pointer-plus-length values carry bounds; safe indexing checks bounds or is proven safe.
- **Drop:** deterministic reverse declaration order; cleanup paths are inserted on every control-flow exit.
- **Arithmetic:** checked by default; wrapping and saturating operators are distinct semantics.
- **Optionals:** tagged option types; pointer niche optimization is permitted only when ABI and validity rules prove it sound.

A region allocator is not a substitute for borrow checking. Runtime tests alone cannot establish memory safety.

## Types and language semantics

The type system includes fixed-width integers, floats, booleans, UTF-8 strings/slices, arrays, tuples, structs, enums with payloads, option/result types, function types, traits, and explicit pointer/ABI types. Exhaustive matching is a compile-time property. Generic monomorphization and compile-time evaluation must be bounded and deterministic.

`|>` passes the left expression as the first argument. `??` unwraps an optional with a fallback. `+%` is wrapping addition; `+|` is saturating addition. More than two call arguments require labels in canonical source mode. Effects (I/O, allocation, mutation, unsafe, async) are explicit in function signatures or verified effect declarations.

## Web and WASM boundary

The web layer is a typed host binding, not a second dynamic language. DOM nodes, events, Canvas, WebGL, WebGPU, Fetch and AudioContext are represented by capability-bearing handles. Signals compile to direct dependency updates; no Virtual DOM is required. UI syntax lowers through the same AST and typed IR. Strings are escaped by default; trusted HTML requires a distinct unsafe-capability type.

The browser still supplies Web APIs and a JavaScript host boundary where the platform requires it. MOST removes application-framework dependence; it cannot make browser APIs cease to exist. Server rendering, hydration, routing and CSS scoping are separate milestones.

## Native and C interoperability

C ABI declarations must specify layout, alignment, calling convention, ownership and error mapping. Header ingestion begins with a constrained declarator parser; full preprocessing and arbitrary macro evaluation are not assumed. SIMD abstractions lower per target with scalar fallbacks. Endian wrappers and bit-width integers have explicit serialization rules. Bare-metal targets require a documented target description and linker/runtime contract.

## 66-rule implementation ledger

| Rules | Area | Required gate |
|---|---|---|
| 1–11 | Identity, autonomy, canonical source, static semantics, deterministic errors and compiler | Grammar, semantic checker, freestanding compiler bootstrap, deterministic artifact tests |
| 12–22 | Regions, pointers, linear resources, slices, arenas, layout and drop | Ownership/region checker, allocator tests, ABI/layout fixtures, unsafe boundary tests |
| 23–33 | Types, pattern matching, extensions, pipelines, strings, named calls, comptime and units | Parser/AST, type inference, exhaustiveness, constant evaluator and semantic conformance |
| 34–44 | DOM, signals, declarative UI, Web APIs, serialization, CSS, async, routing and hydration | WASM backend, browser host tests, direct DOM update tests, XSS and hydration fixtures |
| 45–55 | C ABI, headers, SIMD, endian, bitfields, concurrency, assembly, cross-compilation, mmap and profiling | Native backend, target matrix, FFI ABI tests, sanitizer and race tests |
| 56–66 | Tests, fuzzing, docs tests, stack/resource analysis, conditional compilation, reproducibility, crypto, packages, headers/docs, contracts and frozen core | CI gates, fuzz corpus, deterministic builds, cryptographic vectors and compatibility suite |

## Delivery phases and truthful status

- **M0 — Native lexical base:** C17 scanner, source locations, MOST keywords/operators. This branch implements this phase.
- **M1 — Grammar:** declarations, expressions, blocks, functions, structs/enums, Pratt expressions, parser diagnostics.
- **M2 — Semantic core:** symbol tables, static types, inference, ADTs, exhaustive match, contracts and typed IR.
- **M3 — Safe memory:** regions, borrows, move/linear checking, slices, drop elaboration and allocator interfaces.
- **M4 — Native executable:** portable object/ELF first, then PE and Mach-O; C ABI and target-specific codegen.
- **M5 — WASM:** WASI and browser WASM targets, host bindings, UI and signals.
- **M6 — Toolchain:** tests, fuzzing, docs tests, profiler, reproducible builds, package hashes and self-hosting.

No claim of sub-5-MB self-hosting, full C-header parsing, 15-KB universal web bundles, constant-time cryptography, all-platform cross-compilation, or 30-year ABI stability is made until independently measured and tested.

## Compatibility policy

The 1.0 core grammar and semantics are frozen. Additions after 1.0 use versioned standard-library modules or explicitly versioned language editions; security fixes and compiler bug fixes must not silently change valid program meaning. Binary ABI stability is a separate promise from source compatibility.


## 147-feature architecture extension

The extended architecture backlog, including all 147 proposed capabilities, semantic constraints, platform caveats, duplicate resolution, implementation waves and truthful status ledger, is maintained in [MOST_147_FEATURE_REGISTRY.md](MOST_147_FEATURE_REGISTRY.md). The registry extends the 66 foundational rules; it does not imply that the listed features are already implemented. The canonical numbering is normalized to seven non-overlapping groups (1–21 through 127–147).
