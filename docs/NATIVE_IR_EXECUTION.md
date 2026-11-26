# Native typed compiler IR v1

The native C17 core now exposes a shared typed HIR/MIR/LIR contract in:

- `include/reaper/compiler_ir.h`
- `src/compiler_ir.c`

This is a compiler-core API, not a claim that every Reaper source construct is already lowered through it.

## Pipeline

```text
Reaper lexer/parser AST (expression subset)
  -> typed HIR with source spans
  -> stage/type/operand/source-span verification
  -> MIR lowering and reduced-motion normalization
  -> LIR target lowering
  -> deterministic C17 instruction-table emission
  -> host C17 compiler
```

## Native AST frontend

`reaper_compiler_ir_lower_ast_to_hir` consumes the existing native C17 expression AST and produces typed HIR directly from source-located nodes. The current accepted subset is:

- signed i64 integer literals;
- finite decimal literals using the Reaper lexer's decimal grammar, parsed independently of host numeric locale;
- decoded string literals (including empty strings and escaped quote/newline/tab/return bytes) within the fixed HIR text bound;
- boolean literals;
- unary `+` and `-` over i64 or f64;
- binary `+`, `-`, `*` and `/` over two matching i64 operands or two matching f64 operands.

Mixed i64/f64 arithmetic is rejected. The current subset does not add implicit numeric promotion or decimal remainder/exponent operators.

Every emitted node carries the original source name, line and column. The frontend validates the AST's topological references and rejects unreachable nodes, unknown identifiers, `nothing`/null, unsupported operators and non-i64 arithmetic rather than assigning guessed types. Decimal/text literal values are represented in HIR and same-type f64 arithmetic is lowered through MIR/LIR. Name resolution, function calls, mixed numeric promotion and module semantics remain outside this frontend.

## Current v1 node coverage

| Node family | HIR | MIR | LIR |
|---|---:|---:|---:|
| Typed constants | yes | yes | yes |
| Names | yes | yes | yes |
| Unary i64 operations | yes | yes | yes |
| Binary i64 arithmetic (+, -, *, /) | yes | yes | yes |
| Typed function-call node | yes | yes | yes |
| Aesthetic color/font/metric/motion/accessibility roles | yes | property operations | native property records |

Every node carries a typed value contract, operand indices and an optional source span. Operands must refer to earlier nodes, keeping the current expression graph acyclic. Numeric values must be finite; colors must be exact hexadecimal RGB values; durations, ratios and booleans have bounded representations.

Reduced-motion is a module-level lowering rule: declared motion durations become zero and easing is normalized to linear in MIR.

## Native C17 output

`reaper_compiler_ir_emit_c17` emits a deterministic C17 static instruction table with target metadata and typed values. The native CMake build compiles the generated source as an additional build target. CTest covers IR verification/lowering/emission and SHA-256 vectors.

This validates a bounded native expression AST-to-HIR frontend, the typed IR and generated-C contract. It does **not** yet mean complete Reaper programs or imported `.rpr` module graphs are compiled to C17. Semantic name resolution, module declarations/imports, functions/calls, collections, complete control-flow, effects/ownership, runtime calls, complete SourceMap integration and differential parity are still separate compiler milestones.

## Error contract

Failures return zero and fill `ReaperCompilerIrError` with the affected node index and a bounded diagnostic. The verifier rejects mismatched stages, unsupported operations, malformed spans, invalid values and invalid or forward operand references. It does not silently coerce unknown types.

Python remains the reference runtime for language features outside the current native compiler subset.
