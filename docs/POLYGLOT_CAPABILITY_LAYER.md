# Polyglot capability layer

**Project:** Reaper  
**Maintainer:** Ivan-VHS  
**Status:** capability architecture; conservative static checker implemented  
**Scope:** shared language semantics, standard-library contracts, compiler backends and host interoperability

## Design decision

Reaper remains one language with one canonical lexer, parser, AST, semantic model, runtime and versioned compiler IR. The Java, Kotlin, Swift, TypeScript, Go, C++, Rust, Zig, D, Nim, F#, Scala, Elixir, OCaml and Julia ecosystems are capability references—not fifteen syntaxes to concatenate and not a promise that their libraries or runtimes are embedded.

A capability is considered implemented only when its source contract, runtime/compiler path, tests and supported-target evidence exist together. A reserved token, catalogue record, editor colour or documentation example is not executable support.

## Capability map

| Capability family | Inspiration | Reaper status | Integration boundary |
|---|---|---|---|
| Aggregate snapshot integrity audit | Reaper-owned deterministic systems API | **Native C17 core implemented; .rpr binding pending** | Validates bounded snapshot manifests and diffs aggregate shard metadata only. No record-level linkage, personal-data hydration, external connectors or writes. The language-level feature remains specified until typed runtime/IR parity exists. |
| Static type inference and diagnostics | C#, Java, Kotlin, Swift, TypeScript, F#, OCaml | **Partial — integrated into the reference toolchain** | `reaper --check` runs the same AST type pass by default; `reaper typecheck` provides focused diagnostics, and Studio/LSP use the same checker. It infers primitive/list types and checks supported expressions, mutability, indexes and function arity. Unknown module/FFI values stay `Any`. |
| Nullability and explicit absence | Kotlin, Swift, Rust, OCaml | **Partial** | `nothing` is represented by the current runtime. The checker can preserve an inferred optional union, but there are no source annotations, flow-sensitive null refinement or exhaustive optional handling yet. |
| Generics and parametric collections | Java, Kotlin, TypeScript, C++, Rust, Scala, D | **Partial** | Generic collection shape is inferred for list expressions and selected built-ins. User-declared generic functions, constraints and monomorphization are not implemented. |
| Algebraic data types and pattern matching | F#, Scala, Rust, OCaml, Swift | **Planned** | Requires canonical enum/record declarations, exhaustive match checking and equivalent runtime/IR semantics. |
| Traits, interfaces and protocols | Java, Kotlin, Swift, TypeScript, Go, Rust, Scala | **Planned** | Requires coherent conformance, method lookup, visibility and dispatch rules. Reserved spellings are not proof of support. |
| Async functions and structured concurrency | Kotlin, Swift, Java, Go | **Host-side foundation only** | Python modules already expose asynchronous host APIs in isolated subsystems. The .rpr grammar/runtime does not yet implement language-level `async`, `await`, cancellation or structured task scopes. |
| Channels, actors and supervision | Go, Elixir, Scala | **Planned** | Requires bounded mailboxes, lifecycle ownership, cancellation, supervision policy and deterministic tests. |
| Ownership, borrowing and deterministic destruction | Rust, C++, Swift, D | **Partial runtime foundation** | Reaper has a managed heap, explicit resource handles, regions and opt-in FFI. Static borrow checking, lifetimes, move semantics and general deterministic drops are not yet implemented. |
| Compile-time evaluation and macros | Zig, Nim, D, Rust | **Planned** | AOT currently accepts a limited scalar subset and emits C17. It is not a general `comptime` evaluator, hygienic macro system or self-hosted compiler. |
| Contracts and invariants | D, Eiffel-style design by contract | **Partial** | Runtime assertion and bounded execution exist. Compile-time pre/postcondition proof and general `requires`/`ensures` semantics are not implemented. |
| Multiple dispatch and specialization | Julia, C++ templates, Scala | **Planned** | Requires overload resolution, ambiguity diagnostics, specialization policy and reproducible backend behavior. |
| Native ABI and foreign-function interop | C++, Swift, Rust, D, OCaml | **Available with explicit host permission** | C ABI libraries can be loaded through the existing opt-in FFI bridge. Native FFI remains disabled unless the host explicitly enables it. |
| Native compilation | C++, Rust, Zig, Nim, OCaml, Julia | **Experimental partial** | The current native path lowers a scalar .rpr subset to C17 and invokes a host GCC/Clang-compatible compiler. It is not a full native backend or JIT. |
| Modules and package boundaries | Java, Kotlin, Go, TypeScript, Scala | **Available in the reference runtime** | Existing `import`/`export` module loading remains canonical; package distribution and dependency resolution have separate maturity boundaries. |
| Cross-platform toolchain discovery | All listed ecosystems | **Available as read-only inventory** | Existing language matrix and PATH inventory can identify toolchain candidates. Discovery does not install or execute a compiler. |

## The first delivered increment

The `reaper.typecheck` module adds a conservative semantic pass over the existing AST. It is now wired into the normal `reaper --check` workflow, Studio's native diagnostics tab and LSP:

- infers `Int`, `Float`, `Bool`, `Text`, `Nothing` and list element types;
- unifies numeric and heterogeneous collection element types conservatively;
- checks numeric operators and text concatenation;
- checks sequence indexes and iteration targets;
- catches reassignment to immutable bindings and incompatible mutation of typed bindings;
- checks known built-in and user-function arity;
- understands current collection pipeline result shapes;
- leaves unknown imported, host and FFI contracts as `Any` rather than inventing types;
- reports source line/column diagnostics and supports JSON output.

Use the integrated check from the repository root:

```sh
python -m reaper --check path/to/program.rpr
python -m reaper typecheck path/to/program.rpr --json
python -m reaper --check --syntax-only path/to/program.rpr
```

`--check` now runs syntax parsing and the conservative type pass by default. Use `--syntax-only` only when a parser-only check is needed for compatibility. Normal program execution, tree-walk runtime and VM semantics remain unchanged; static diagnostics never execute the selected source. The checker is not yet a complete sound type system: parameters have no source-level annotations, generic user declarations are absent, and type inference across external module boundaries remains intentionally unknown.

## Snapshot integrity audit increment

The native C17 core in include/reaper/snapshot_audit.h validates bounded manifests and compares sorted shard aggregates. It also offers a fixed-length transient comparison primitive that does not allocate, copy, log or retain its input. The core is offline and read-only. It does not provide row-level joins, personal-data processing, external I/O or mutation APIs. The .rpr standard-library facade and typed IR/runtime parity have not yet been implemented; see [the capability contract](SNAPSHOT_INTEGRITY_CAPABILITY.md).

## Implementation order

1. **Type foundation:** stabilize diagnostics and inference; add source-level type annotations, explicit `Option`/`Result`, and typed function signatures.
2. **Core data model:** add structs/enums, pattern matching, exhaustiveness checks, traits/protocols and generic constraints to one grammar and AST.
3. **Resource safety:** formalize ownership, borrowing, lifetimes, deterministic cleanup, regions and safe FFI boundaries.
4. **Concurrency:** implement language-level async tasks, cancellation, channels, bounded scheduling and actor supervision with a deterministic test scheduler.
5. **Compile-time and optimization:** introduce versioned typed IR, constant evaluation, hygienic compile-time extensions, optimization passes and differential conformance fixtures.
6. **Backend parity:** expand native lowering in measured stages; compare native and reference results before promoting a feature to stable.
7. **Studio integration:** surface the same diagnostics, type information, IR and capability maturity through LSP and the desktop workbench.

Each stage must preserve existing .rpr behavior and publish its own tests. Features that require OS privileges, physical hardware or external compilers remain explicit host adapters; Reaper source must never silently acquire those permissions.
