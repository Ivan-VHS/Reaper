# 1,000-program adoption map: Reaper

This file assigns the language-tooling portion of the supplied 1,000-item catalogue. It records adoption themes rather than cloning complete external IDEs, compilers or runtimes.

## Ownership within the catalogue

| Catalogue IDs | Original subject area | Reaper treatment |
|---|---|---|
| 251–310 | Languages, runtimes, VM and language design | Language semantics, reference runtime, VM and safe extension model |
| 311–360 | Editors, language servers and debuggers | Studio, LSP, DAP, completion, navigation, diagnostics and editor protocol support |
| 361–420 | Build systems, package managers, tests and formatters | Reproducible toolchain commands, dependency and CI contracts, formatting/lint integration |
| 421–470 | Parser generators, compiler IR, JIT, WASM and REPLs | Lexer/parser, AST/IR, checked lowering, VM and language conformance |
| 471–500 | Documentation, playgrounds and code presentation | Versioned language docs, syntax highlighting, samples and local test playgrounds |

## First implementation wave

- **LSP Semantic Tokens** — textDocument/semanticTokens/full, a declared legend and delta-encoded tokens for keywords, functions, variables, comments, strings, numbers and operators.
- Token coordinates use UTF-16 code units as required by LSP. The pass is lexical, bounded to an open document, and does not execute source or claim type inference.
- **LSP Formatting** — `textDocument/formatting` now returns a single bounded full-document edit using the in-repository whitespace formatter. It normalizes indentation and trailing whitespace without rewriting tokens.
- **Toolchain Inventory and Lock** — `reaper-toolchain` discovers compiler, build, formatter, parser, debugger and WASM executables by PATH lookup only. Explicit locks pin resolved paths and SHA-256 contents; no discovered tool is launched.

## Adoption rules

1. Python remains the compatibility reference until native C17 passes conformance tests; do not claim language parity because a grammar or catalogue entry exists.
2. LSP/DAP capabilities must be advertised only when implemented and covered by protocol tests.
3. Workspace services index explicitly opened buffers under documented size/document limits. No implicit disk crawler or remote code index.
4. Compiler optimizations and JIT/WASM features require a measurable, deterministic baseline and explicit execution quotas.
5. External formatters, linters, compilers and runtimes are optional adapters; no copied GPL implementation is bundled into the Apache-2.0 repository.
6. Playground execution remains local and sandboxed; online execution providers are not required.

## Remaining backlog themes

The 251–310 cluster prioritizes language conformance and effect/type modelling. The 311–360 cluster prioritizes semantic tokens, formatting, code actions, signature help, DAP capabilities and protocol replay tests. The 361–420 cluster prioritizes lockfile integrity, reproducible toolchain profiles, formatter contracts, CI matrix helpers and property-based tests. The 421–470 cluster prioritizes parser recovery, source maps, IR verification, bytecode inspection and deterministic REPL state. The 471–500 cluster prioritizes versioned reference docs, runnable examples and link/style verification.

Every capability remains proposed until its protocol/runtime tests and boundary are recorded.
