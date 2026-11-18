# Reaper architecture — standalone language and interpreter

## Product boundary

Reaper is an independent, flow-first programming language. Its 0.1 implementation is a Python 3.10+ tree-walking interpreter with a lexer, parser, runtime, CLI, examples and standard-library tests. It is not a compiler, operating system, package registry, plugin host or autonomous agent.

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

## MCST Elbrus E2K target profile

The --target-info CLI option reports host architecture metadata from Python's platform module. An E2K host is labelled VLIW/E2K, but the active execution backend remains the Python tree-walk interpreter. This report is host discovery, not cross-compilation target selection, compiler identification, native code generation or a hardware capability probe.

See [ELBRUS_E2K.md](ELBRUS_E2K.md) for the AETHER-ANAS mapping, MCST references and staged native-backend acceptance gates.
