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

## IR contract in this increment

The first IR slice is deliberately small and backend-neutral:
- nodes are stored in a caller-owned immutable array;
- each operand refers only to an earlier node, giving a deterministic topological order;
- source line/column are carried for later diagnostics;
- the verifier checks opcode, result type, operand presence, reference bounds and operand types;
- no parser, optimizer, ownership proof or machine-code generator is claimed.

Supported operations are integer constant, signed 64-bit addition (semantic overflow policy still needs to be fixed before lowering), and return. The next semantic increment must define checked/wrapping/saturating arithmetic explicitly and add a typed AST-to-IR lowering path.

## Build and test

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

This increment does not remove Python from the repository or claim native interpreter parity. The independent C17 migration policy remains in force until the complete compatibility suite passes.
