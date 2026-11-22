# Reaper language roadmap — editions 0.3 to 1.0

This roadmap expands Reaper by **verified language slices**, not by fabricating function counts. Every item moves through the same acceptance path:

1. Syntax and source-span rules.
2. Written value model and semantic rules.
3. Tree-walk reference behavior.
4. Canonical IR and VM behavior.
5. Negative, boundary, resource-limit and differential tests.
6. LSP/IDE diagnostics and completion.
7. Documentation, feature-registry maturity and migration notes.

A feature is `implemented` only when all required execution paths are covered. It becomes `verified` only after CI evidence, including supported Python versions and native checks where applicable. Catalogue entries, aliases and names alone do not count as functionality.

## Edition targets

| Edition | Language milestone | Required outcomes | Status |
|---|---|---|---|
| 0.2 | Core modern syntax | `let/const/mut`, functions/return, conditionals, loops, break/continue, maps, field lookup, membership, lazy null coalescing | Implemented in Python reference + VM; CI validation pending |
| 0.3 | Types and algebraic data | explicit primitive types, type declarations, structs, enums, Option/Result, pattern matching | Planned |
| 0.4 | Modules and packages | canonical module namespaces, package manifest, semantic versions, lockfile, offline dependency resolution, formatter and documentation generator | Planned |
| 0.5 | Collection and iteration model | iterator protocol, lazy pipelines, generators, comprehensions, immutable collections and deterministic iteration contracts | Planned |
| 0.6 | Effects and concurrency | explicit effect declarations, capability-scoped IO, async/await, cancellation, tasks, channels and bounded concurrency | Planned |
| 0.7 | Compiler and native execution | typed IR, control-flow verifier, bytecode format, C17 implementation parity and reproducible native build | Planned |
| 0.8 | Developer toolchain | language server semantic index, formatter, linter, test runner, package inspection, debugger parity and profiling format | Planned |
| 0.9 | Compatibility hardening | conformance corpus, fuzzing, differential engines, ABI/API review, migration tooling and reproducible releases | Planned |
| 1.0 | Stable language edition | frozen core grammar, normative specification, stable standard-library contracts, semantic versioning and compatibility policy | Not started |

## 0.3 — type and data model

Proposed syntax (illustrative until the parser, type checker and runtime implement it):

```reaper
type UserId = i64

struct User {
    id: UserId
    name: text
}

enum Lookup {
    found(User)
    missing
}

fn display_name(value: Lookup) -> text {
    match value {
        found(user) => user.name
        missing => "unknown"
    }
}
```

Acceptance requires duplicate-field detection, type mismatch diagnostics with source spans, exhaustiveness rules, deterministic layout metadata where needed, and identical behavior across supported engines. No type annotations in this example should be treated as supported by 0.2.

## 0.4 — package and module toolchain

A package must have a manifest, explicit entry points, version constraints, a lockfile, source integrity metadata and documented capabilities. Resolution must be deterministic and able to work offline from verified local cache. Import cycles, path traversal, dependency ambiguity and oversized archives must be rejected.

Expected user-facing commands: `reaper fmt`, `reaper lint`, `reaper test`, `reaper package check`, `reaper deps lock`. These commands are roadmap targets, not currently shipped commands.

## 0.5 — iteration and data model

Introduce lazy iterators only with explicit resource limits and cancellation. A lazy pipeline must preserve error location and deterministic ordering. Collection transformations should avoid materializing unbounded sequences. Comprehensions and generators must be checked against the existing step, heap, text and collection quotas.

## 0.6 — effects and concurrency

Ordinary expressions remain pure by default. Filesystem, network, clock, process and native calls require explicit capabilities. Async tasks, channels, cancellation and scheduling must be bounded, testable and deterministic where possible. No implicit background execution or unrestricted host access is introduced by language syntax.

## 0.7–1.0 — native compiler and stability

The C17 track must reach differential conformance with the Python reference before it can be called a complete compiler backend. Required milestones include typed IR, structural and control-flow verification, stack and memory safety, bytecode/ABI versioning, scalar reference checks, sanitizer runs, fuzzing and cross-platform release artefacts.

The 1.0 gate requires:
- the same normative syntax and observable semantics across reference and native engines;
- stable module, package, standard-library and runtime APIs;
- explicit resource and capability guarantees;
- a published conformance corpus and migration policy;
- no known silent semantic divergence in release-blocking tests.

## Iteration policy

The imagined 64,564,654 iterations and hundreds of millions of functions are not treated as literal implementation quantities. A huge synthetic function catalogue would make the language less coherent and would not create executable capabilities. Reaper grows through small, traceable increments whose value is demonstrated by behavior, tests and documentation.

The immediate next milestone after 0.2 is the 0.3 type system: type syntax, inference boundaries, structs/enums, Option/Result and exhaustive pattern matching, built as one end-to-end vertical slice.
