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
