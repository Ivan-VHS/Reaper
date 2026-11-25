# Feature matrix

| Component | Current scope | Status |
|---|---|---|
| Python runtime | lexer, parser, interpreter, CLI, REPL, modules | available |
| Static type analysis | conservative AST inference, numeric/operator checks, collection/index checks, mutability and call-arity diagnostics | partial; built into `reaper --check`, Studio and LSP; static-only, no source execution |
| Quotas/resources | steps, calls, collections, text, heap, open handles | reference runtime |
| Division | Euclidean divmod, quotient/remainder, divisibility | implemented |
| Allocation | partition/split, distribute, weighted allocation | implemented |
| Audit/governance | explicit grants, HMAC scope, TTL/revocation | reference runtime |
| Studio | Windows editor/debugger, command palette, MCU profile and hardware-boundary overview | desktop app; no live device inspector |
| CODEX-66 | searchable 66-item native feature catalogue with JSON export and maturity labels | implemented metadata/UI; feature statuses remain evidence-based |
| Native C17 | lexer, expression Pratt parser, owned AST, checked i64 IR, constant folding and limited lowering | partial |
| Native MMIO contract | checked region/register descriptors, widths, bounds, alignment, access policies, capability checks and adapter callbacks | implemented C API; no physical mapping or device driver |
| LSP semantic tokens and diagnostics | lexical highlighting plus local inferred-type diagnostics from the reference AST checker | stdio LSP; UTF-16 positions; no cross-file type inference |
| МОСТ | 54 aliases: 21 executable, 33 reserved | mixed |
| QCS | separate lexer/parser/JSON AST | validation tool |
| THESIS | versioned assertion/evidence graph | no auto-verification |
| Pytyliki | optional C ABI metric calls | explicit trusted path |
| Registries | 813 proposals; canonical API contract registry; canonical symbolic-token catalogue | specification, not completion |

Python remains the compatibility reference. Native C17 is not yet a full interpreter or general machine-code backend. The MMIO API is a checked adapter contract, not a complete hardware runtime. The systems-language migration and maturity gates are documented in [HARDWARE_LANGUAGE.md](HARDWARE_LANGUAGE.md).
