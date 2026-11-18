# Reaper architecture — standalone language and interpreter

## Product boundary

Reaper is an independent, flow-first programming language. Its 0.1 implementation is a Python 3.10+ tree-walking interpreter with a lexer, parser, runtime, CLI, examples and standard-library tests. It is not a native-code compiler, operating system, package registry, plugin host or autonomous agent.

The goal is one coherent language product with separable implementation layers. Reaper must remain independently installable and executable; integration with another project is optional and must use a stable adapter rather than make that project a runtime dependency.

## Runtime layers

1. **CLI** — argument parsing, UTF-8 source loading, check-only mode, system catalogues and controlled interpreter invocation.
2. **Lexer** — deterministic tokenization with source locations and explicit lexical errors.
3. **Parser** — recursive-descent statements and Pratt expressions; the AST is the parser/runtime contract.
4. **Runtime** — lexical environments, immutable/mutable bindings, functions, built-ins, flow composition and bounded execution.
5. **Experimental host systems** — reaper.reaper_systems contains nine opt-in reference APIs for relays, epochs, effects, profiling, canonical IR, guarded FFI, snapshots, actors and health supervision. They do not alter .rpr semantics or silently grant host privileges.
6. **Diagnostics** — user-facing errors retain file, line and column where a source token exists.
7. **Examples and conformance tests** — executable language examples and regression coverage for lexical, syntactic and runtime semantics, plus isolated tests for the host-system prototypes.
8. **Packaging** — a standard Python package with a CLI entry point and no third-party runtime dependencies.

## Data and control flow

Source text → lexer tokens → parser AST → bounded tree-walk runtime → explicit console output.

The language has no implicit file, network, clock, process, shell or hardware access. Console input/output is explicit through language operations. New effects require a separately designed capability interface, documented permissions and tests; they are not added as hidden built-ins.

## Resource model

The interpreter exposes independent limits for executed steps, function-call depth, collection item count and text-concatenation length. Limits must be validated as positive values, checked before materialization when practical, and surfaced as language errors. The defaults are guardrails, not a security sandbox or proof against all denial-of-service inputs.

The experimental actor API also bounds mailbox length; the snapshot codec bounds serialized byte length. These checks do not imply a global memory quota or hard-real-time scheduling.

## Extension rules

- Preserve source compatibility or document a deliberate language-version break.
- Keep lexer, parser, runtime and CLI responsibilities separate.
- Keep semantics deterministic and testable.
- Add built-ins only with explicit argument validation, bounded work and documented effects.
- Keep I/O effects explicit; never silently grant filesystem, network or process access.
- Keep Python as the implementation host for the current milestone; native compilation and self-hosting are future work.
- Keep optional tooling outside the interpreter's required runtime dependency set.
- Treat architecture metaphors as design prompts, not performance proofs: zero-cost, O(1), microsecond, JIT and distributed guarantees require dedicated implementations and reproducible acceptance evidence.
- Keep experimental host APIs opt-in until their semantics can be integrated into a versioned language edition.

See [REAPERS_ARCHITECTURE.md](REAPERS_ARCHITECTURE.md) for the nine-system contract catalogue, implementation boundaries and tests.
