# Native typed compiler IR v1

The native C17 core now exposes a shared typed HIR/MIR/LIR contract in:

- `include/reaper/compiler_ir.h`
- `src/compiler_ir.c`

This is a compiler-core API, not a claim that every Reaper source construct is already lowered through it.

## Pipeline

```text
typed HIR
  -> stage/type/operand/source-span verification
  -> MIR lowering and reduced-motion normalization
  -> LIR target lowering
  -> deterministic C17 instruction-table emission
  -> host C17 compiler
```

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

This validates the typed IR and generated-C contract. It does **not** yet mean the complete Reaper grammar or imported `.rpr` module graph is compiled to C17. Parser-to-general-HIR mapping, complete source maps, control-flow/collection/effect lowering, native runtime calls and differential parity are still separate compiler milestones.

## Error contract

Failures return zero and fill `ReaperCompilerIrError` with the affected node index and a bounded diagnostic. The verifier rejects mismatched stages, unsupported operations, malformed spans, invalid values and invalid or forward operand references. It does not silently coerce unknown types.

Python remains the reference runtime for language features outside the current native compiler subset.
