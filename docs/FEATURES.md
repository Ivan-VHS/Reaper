# Feature matrix

| Component | Current scope | Status |
|---|---|---|
| Python runtime | lexer, parser, interpreter, CLI, REPL, modules | available |
| Quotas/resources | steps, calls, collections, text, heap, open handles | reference runtime |
| Division | Euclidean divmod, quotient/remainder, divisibility | implemented |
| Allocation | partition/split, distribute, weighted allocation | implemented |
| Audit/governance | explicit grants, HMAC scope, TTL/revocation | reference runtime |
| Studio | Windows editor, debug, call stack, local completion and current-document symbol navigation | desktop app |
| CODEX-66 | searchable 66-item native feature catalogue with JSON export and maturity labels | implemented metadata/UI; feature statuses remain evidence-based |
| Native C17 | lexer, expression Pratt parser, owned AST, checked IR | partial |
| Freestanding OS toolchain | C17/assembly bridge, ELF linking, x86_64/AArch64/RISC-V target selection, MMIO/atomic/arena helpers | experimental; does not compile .rpr to machine code |
| LSP semantic tokens | lexical highlighting for keywords, identifiers, strings, numbers and operators | stdio LSP; UTF-16 positions; no type inference |
| МОСТ | 54 aliases: 21 executable, 33 reserved | mixed |
| QCS | separate lexer/parser/JSON AST | validation tool |
| THESIS | versioned assertion/evidence graph | no auto-verification |
| Pytyliki | optional C ABI metric calls | explicit trusted path |
| Registries | 813 proposals; 666 API contracts; 666 symbolic lexemes | specification, not completion |

Python remains the compatibility reference. Native C17 is not yet a full interpreter.
