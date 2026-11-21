# Engineering gates

| # | Gate | Acceptance |
|---:|---|---|
| 1 | Semantics | one grammar, parser and canonical AST |
| 2 | Effects | host I/O explicit; no implicit privilege |
| 3 | Bounds | steps, recursion, collections, text, imports and resources limited |
| 4 | Errors | source-aware diagnostics; fail closed |
| 5 | MOST | exact alias mapping only; no second grammar |
| 6 | Native | C17 parity claimed only after conformance tests |
| 7 | Interop | versioned schemas/ABI; explicit trusted native path |
| 8 | Evidence | separate implemented / partial / proposed |
| 9 | Release | tests, examples, packaging, screenshot/link checks and license |

Python remains the current compatibility reference. Native code executes in-process and is not a sandbox for untrusted extensions.

## Shared evolution matrix

This repository adopts the shared [Engineering Evolution Framework](ENGINEERING_EVOLUTION_FRAMEWORK.md): 20 domains, 40 practices, a versioned JSON contract and negative tests. The framework complements existing engineering, project and safety contracts; it does not assert that every technique is applicable or already implemented. Claims of implementation must remain backed by local code, tests or operational evidence.
