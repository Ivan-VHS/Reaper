# MOST implementation status in Reaper

**Branch:** `feat/most-semantic-ir`  
**Scope:** first executable semantic-IR foundation, layered over the C17 lexer.  
**Status vocabulary:** `implemented` means executable code and tests exist; `specified` means a written contract exists; `planned` means not yet implemented.

## Architecture slices

| Slice | Current state | Evidence / next gate |
|---|---|---|
| C17 build and native lexer | implemented on parent branch | CMake target and lexer tests |
| MOST lexical vocabulary | implemented on parent branch | keyword/operator lexer tests; grammar is not implied |
| Semantic IR data model | implemented in this branch | `include/reaper/ir.h` |
| IR structural verifier | implemented in this branch | `src/ir.c`, `tests/test_ir.c` |
| Parser and AST | planned | declarations, Pratt expressions, source spans |
| Name resolution and static type checker | planned | symbol tables, inference, ADT/exhaustiveness tests |
| Ownership, borrow and region analysis | specified | CFG-based move/borrow checking and negative tests |
| Effect/capability checking | specified | explicit effect rows and denied-capability tests |
| Native code generation | planned | target ABI and executable conformance fixtures |
| WASM/Web Core | specified | WASI/browser host tests and capability boundary |
| 147-feature registry | specified | seven numbered groups; feature-by-feature acceptance gates |
| 813-feature architecture map | specified | `docs/REAPER_813_FEATURE_ARCHITECTURE.md`; seven new ranges 148–813 mapped to compiler, type system, runtime, stdlib, security, tooling and host layers |
| MOST bilingual bridge | planned | M2 after parser/AST; canonical symbols, scoped domain dictionaries, ambiguity diagnostics and equivalent IR tests |

## IR contract in this increment

The first IR slice is deliberately small and backend-neutral:
- nodes are stored in a caller-owned immutable array;
- each operand refers only to an earlier node, giving a deterministic topological order;
- source line/column are carried for later diagnostics;
- the verifier checks opcode, result type, operand presence, reference bounds and operand types;
- no parser, optimizer, ownership proof or machine-code generator is claimed.

Supported operations are integer constant, signed 64-bit addition (semantic overflow policy still needs to be fixed before lowering), and return. The next semantic increment must define checked/wrapping/saturating arithmetic explicitly and add a typed AST-to-IR lowering path.

## Expanded 813-feature roadmap

The original 147-feature registry remains intact. The continuation (148–813) is mapped in `docs/REAPER_813_FEATURE_ARCHITECTURE.md` into stable ranges: 148–220 bilingual frontend/MOST bridge; 221–310 types and mathematics; 311–410 concurrency and memory; 411–510 data and schemas; 511–610 security and resilience; 611–710 developer tooling; 711–813 integrations and host interaction. These are proposals with explicit implementation gates, not implemented APIs.

The architecture separates the Russian MOST layer from REAPER's canonical semantics: both source forms must lower to the same typed AST/IR. Morphology and synonyms may resolve names only; they may not alter types or execution semantics. Ambiguous Russian input must fail with a diagnostic rather than be guessed.

## Next acceptance-gated phase

**M1: Parser + AST + Pratt expressions + source spans.** M2 (MOST name/domain resolver and bilingual lowering) depends on a stable parser and source mapping. Do not implement morphology heuristics in the lexer or create a second runtime for MOST.

## Build and test

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

This increment does not remove Python from the repository or claim native interpreter parity. The independent C17 migration policy remains in force until the complete compatibility suite passes.
