# Reaper architecture — standalone language and interpreter

## Product boundary

Reaper is an independent, flow-first programming language. Its 0.1 implementation includes a Python 3.10+ tree-walking interpreter and an additive static compiler front end that emits portable source-mapped IR. It is not a native-code compiler, operating system, package registry, plugin host or autonomous agent.

The goal is one coherent language product with separable implementation layers. Reaper must remain independently installable and executable; integration with another project is optional and must use a stable adapter rather than make that project a runtime dependency.

## Runtime layers

1. **CLI** — argument parsing, UTF-8 source loading, check-only mode, and controlled interpreter invocation.
2. **Lexer** — deterministic tokenization with source locations and explicit lexical errors.
3. **Parser** — recursive-descent statements and Pratt expressions; the AST is the parser/runtime contract.
4. **Runtime** — lexical environments, immutable/mutable bindings, functions, built-ins, flow composition and bounded execution.
5. **Diagnostics** — user-facing errors retain file, line and column where a source token exists.
6. **Examples and conformance tests** — executable language examples and regression coverage for lexical, syntactic and runtime semantics.
7. **Packaging** — a standard Python package with a CLI entry point and no third-party runtime dependencies.

## Data and control flow

Source text → lexer tokens → parser AST → bounded tree-walk runtime → explicit console output.

The language has no implicit file, network, clock, process, shell or hardware access. Console input/output is explicit through language operations. New effects require a separately designed capability interface, documented permissions and tests; they are not added as hidden built-ins.

## Resource model

The interpreter exposes independent limits for executed steps, function-call depth, collection item count and text-concatenation length. Limits must be validated as positive values, checked before materialization when practical, and surfaced as language errors. The defaults are guardrails, not a security sandbox or proof against all denial-of-service inputs.

## Extension rules

- Preserve source compatibility or document a deliberate language-version break.
- Keep lexer, parser, runtime and CLI responsibilities separate.
- Keep semantics deterministic and testable.
- Add built-ins only with explicit argument validation, bounded work and documented effects.
- Keep I/O effects explicit; never silently grant filesystem, network or process access.
- Keep Python as the implementation host for the current milestone; native compilation and self-hosting are future work.
- Keep optional tooling outside the interpreter's required runtime dependency set.


## Nine-system architecture

The compiler and runtime foundations are composed into nine independently testable host subsystems: typed local routing (`reaper.citadel`), epoch-managed regions (`reaper.resources`), revocable capabilities (`reaper.security`), measured profiling and IR optimization (`reaper.profiling`, `reaper.compiler`), portable semantic IR (`reaper.compiler`), capability-gated C ABI integration (`reaper.interop`), checksummed application-state snapshots (`reaper.checkpoint`), bounded cooperative actors (`reaper.concurrency`) and explicit health supervision (`reaper.vanguard`).

Full contracts, examples, limitations and acceptance gates are maintained in [REAPER_SYSTEMS.md](REAPER_SYSTEMS.md). These APIs do not add implicit network access, background recovery or new .rpr syntax.
