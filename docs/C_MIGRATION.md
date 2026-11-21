# Native C17 migration

Python remains the executable compatibility reference. C17 is a staged native implementation.

| Milestone | Acceptance |
|---|---|
| Lexer | equivalent tokens and source spans |
| Parser M1 | one expression, owned AST, precedence tests |
| IR | checked integer operations and explicit lowering |
| Runtime | differential semantic conformance |
| Release | C17-only build/test only after parity |

Do not remove Python until the complete language and CLI contract passes differential tests.
