# Native Canonical IR Execution

The native Reaper IR verifier now has a deliberately small deterministic executor for its implemented i64 subset.

## Contract

- The input module must pass reaper_ir_verify.
- Supported executable operations are CONST_I64, ADD_I64, SUB_I64, MUL_I64, DIV_I64, and one final RETURN.
- Nodes are evaluated in their verified topological order.
- Caller-owned scratch storage must provide one int64_t slot per IR node; the executor performs no heap allocation and invokes no host effects.
- Signed overflow, division by zero, malformed return structure, invalid IR, and insufficient scratch capacity fail explicitly.
- The result output is changed only after successful completion of the final return. Scratch values are temporary workspace and may contain a computed prefix after an arithmetic failure.

The executor is not a general language runtime, native code generator, or proof of full Reaper language support. Additional opcodes require verifier rules, execution semantics, and tests before they can be used.

## Why this slice exists

This is the first executable bridge between the structurally verified Canonical IR and deterministic local evaluation. It makes arithmetic failure semantics observable and testable instead of relying on unchecked machine behavior.