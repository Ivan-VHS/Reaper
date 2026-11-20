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
8. **Polyglot workspace** — an optional local-first application/library module for target-language profiles, content coverage estimates, contextual phrase cards, spaced repetition and study-session analytics. It is isolated from ordinary `.rpr` execution and uses an atomic, versioned JSON store.

## Polyglot learning subsystem

The optional Polyglot workspace is accessed through `reaper polyglot` and the `PolyglotWorkspace` Python API. It has its own versioned JSON persistence model; it does not add implicit filesystem or network behavior to Reaper source programs.

Its core loop is understandable input → contextual phrase capture → deterministic spaced repetition → learner-reported speaking practice and feedback. The four daily pillars are audio/visual input, contextual reading, retention, and speaking/feedback. Text difficulty is estimated with a transparent vocabulary-coverage heuristic (word units for spaced writing systems and character/phrase coverage for compact scripts); this is not a comprehension test. Speech recognition, media retrieval/playback, dictionary lookup, and automated pronunciation scoring remain optional future adapters. See [POLYGLOT_IMMERSION.md](POLYGLOT_IMMERSION.md).

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
