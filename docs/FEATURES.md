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
| Typed layouts and target profiles | Reaper-native declaration AST bridge and descriptor/layout engine for fixed-width scalars, arrays, struct, union, enum, distinct and opaque data; Windows/Linux/DAK target profiles | partial; main typechecker, canonical typed IR and native ABI lowering remain incomplete |
| Canonical typed IR | Versioned typed nodes, checked source spans and one-to-one SourceMap provenance validation | partial; source parser integration and byte-offset spans remain incomplete |
| Generics and interfaces | Generic parameter binding, bounded constraints, recursive pointer/array/distinct substitution and method-signature conformance | partial; inference, associated-type resolution and native monomorphization remain incomplete |
| Typed HIR/MIR/LIR | Reaper-native HIR/MIR/LIR containers and checked linear lowering with preserved source provenance and virtual registers | partial; CFG/SSA, optimization, physical registers and machine encoding remain incomplete |
| Native aggregate ABI | Bounded SysV x86_64, Microsoft x64 and AAPCS64 classification plus byte-offset aggregate piece plans | partial; field-driven class computation, full register assignment and call-frame lowering remain incomplete |
| ELF/PE object pipeline | Explicit object, linker and loader contracts with fail-closed diagnostics | planned; byte writers, relocation/linking and executable loading are not implemented |
| Target runtime conformance | Host-native scalar AOT smoke execution on Linux, macOS and Windows CI runners | partial; typed aggregate ABI, cross-target execution and DAK runtime are not covered |
| Native MMIO contract | checked region/register descriptors, widths, bounds, alignment, access policies, capability checks and adapter callbacks | implemented C API; no physical mapping or device driver |
| LSP semantic tokens and diagnostics | lexical highlighting plus local inferred-type diagnostics from the reference AST checker | stdio LSP; UTF-16 positions; no cross-file type inference |
| МОСТ | 54 aliases: 21 executable, 33 reserved | mixed |
| QCS | separate lexer/parser/JSON AST | validation tool |
| THESIS | versioned assertion/evidence graph | no auto-verification |
| Pytyliki | optional C ABI metric calls | explicit trusted path |
| Registries | 813 proposals; 666 API contracts; 666 symbolic lexemes | specification, not completion |

Python remains the compatibility reference. Native C17 is not yet a full interpreter or general machine-code backend. The MMIO API is a checked adapter contract, not a complete hardware runtime. The systems-language migration and maturity gates are documented in [HARDWARE_LANGUAGE.md](HARDWARE_LANGUAGE.md).
