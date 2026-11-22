# Feature matrix

| Component | Current scope | Status |
|---|---|---|
| Python runtime | lexer, parser, interpreter, CLI, REPL, modules, structured `attempt/recover/finally/throw` | available; tree-walk and VM parity regression tests added, CI pending |
| Quotas/resources | steps, calls, collections, text, heap, open handles | reference runtime |
| Division | Euclidean divmod, quotient/remainder, divisibility | implemented |
| Allocation | partition/split, distribute, weighted allocation | implemented |
| Audit/governance | explicit grants, HMAC scope, TTL/revocation | reference runtime |
| Studio | Windows editor, debug, call stack, local completion and current-document symbol navigation | desktop app |
| CODEX-66 | searchable 66-item native feature catalogue with JSON export and maturity labels | implemented metadata/UI; feature statuses remain evidence-based |
| Native C17 | lexer, expression Pratt parser, owned AST, checked IR | partial |
| МОСТ | 54 aliases: 21 executable, 33 reserved | mixed |
| QCS | separate lexer/parser/JSON AST | validation tool |
| THESIS | versioned assertion/evidence graph | no auto-verification |
| VentuSample | pack v1 manifest, 22 descriptors, pair comparison | implemented consumer |
| Pytyliki | optional C ABI metric calls | explicit trusted path |
| Registries | 813 proposals; 666 API contracts; 666 symbolic lexemes | specification, not completion |

The structured error-handling construct is implemented in the Python reference runtime and canonical IR/VM. Native C17 grammar and runtime parity remain out of scope for this feature. Python remains the compatibility reference. Native C17 is not yet a full interpreter.
