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
| МОСТ | 54 aliases: 21 executable, 33 reserved | mixed |
| QCS | separate lexer/parser/JSON AST | validation tool |
| THESIS | versioned assertion/evidence graph | no auto-verification |
| VentuSample | pack v1 manifest, 22 descriptors, pair comparison | implemented consumer |
| Pytyliki | optional C ABI metric calls | explicit trusted path |
| OCTA-8 | eight bounded value kinds, deterministic JSON envelope, validate/unpack/digest/map language builtins | implemented in Python reference runtime; C17 parity not claimed |
| CLife | bounded snapshots, SHA-256 verify and safe restore into new directory | implemented Python utility |
| Registries | 813 proposals; 666 API contracts; 666 symbolic lexemes | specification, not completion |

Python remains the compatibility reference. Native C17 is not yet a full interpreter.
