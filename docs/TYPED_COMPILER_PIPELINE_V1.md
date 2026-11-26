# Typed compiler pipeline v1

**Status: partial foundation.** This milestone adds Reaper-written canonical typed IR, source provenance, generic/interface contracts, a bounded HIR/MIR/LIR pass chain and aggregate ABI planning. It deliberately does not claim a finished native compiler. ELF/PE serialization, linking and executable loading remain planned and fail closed.

## 1. Canonical Typed IR, Span and SourceMap

Source: `selfhost/typed_ir.rpr`.

The v1 schemas are:

- `SPAN_V1`: source identity, one-based start line/column and end line/column.
- `TIR_NODE_V1`: stable node id, operation, type identity, effect list, Span, operand ids and payload.
- `SOURCE_MAP_V1`: source identity plus exactly one `SOURCE_MAP_ENTRY_V1` per typed node.
- `TIR_MODULE_V1`: module identity, source name, type table, typed nodes and SourceMap.

The verifier rejects duplicate node ids, missing or duplicate provenance, mismatched source names, malformed spans and dangling operand ids. HIR and MIR preserve the exact Span value and SourceMap entries.

**Boundary:** the existing bootstrap token contract stores `[kind, lexeme, line, column]`; byte offsets are not present. The current Span schema therefore preserves source line/column coordinates and does not invent byte positions. Parser-to-TIR semantic normalization is not yet wired into the main compatibility frontend.

## 2. Generics, constraints and interfaces

Source: `selfhost/generic_types.rpr`.

Implemented contracts include generic parameter lists, interface-name bounds, exact arity/default binding, bound satisfaction against explicit implementation records, structural substitution through pointer/array/distinct descriptors, interface method-signature checking and associated-type presence checking.

**Boundary:** inference, overload resolution, superinterface closure, associated-type substitution, variance, recursive constraint solving, generic parser syntax and native monomorphization are not complete. Interface conformance is descriptor-level validation, not proof that executable method bodies exist.

## 3. HIR, MIR and LIR

Source: `selfhost/typed_lowering.rpr`.

The pass chain is explicit:

`TIR_MODULE_V1 -> HIR_MODULE_V1 -> MIR_MODULE_V1 -> LIR_MODULE_V1`.

The implemented linear operation subset includes constants, copies, add/subtract/multiply, compare, calls, field loads/stores, aggregate construction, phi placeholders and return. MIR-to-LIR assigns virtual registers, resolves only prior value definitions, carries the exact SourceMap and binds LIR to a validated platform whose process ABI is declared.

**Boundary:** this is not a complete CFG/SSA implementation. Branch/switch construction, dominance, phi elimination, optimization, liveness, register allocation, spilling, stack frames, instruction encoding and a final machine-code emitter remain incomplete. A profile-only DAK target is rejected before ABI-dependent LIR is produced.

## 4. Native aggregate ABI classification

Source: `selfhost/native_abi.rpr`.

The v1 classifier returns versioned plans, not executable call sequences:

- SysV AMD64 accepts caller-supplied per-eightbyte `INTEGER`/`SSE` classes for aggregates up to 16 bytes, with memory fallback for larger or explicitly unaligned aggregates.
- Microsoft x64 classifies 1/2/4/8-byte aggregates as direct GPR values and other sizes as indirect caller storage.
- AAPCS64 recognizes declared homogeneous `f32`/`f64` aggregates of one to four elements, otherwise uses direct GP passing up to 16 bytes and indirect passing above that.

The `native_abi_lower_aggregate` pass expands the selected policy into explicit byte-offset pieces (SysV eightbytes, AAPCS64 HFA/GP chunks, or an indirect pointer). The result still explicitly remains `register_assignment_and_stack_frame_pending`.

**Boundary:** SysV field merging and class derivation are not yet computed from actual aggregate field trees; SSEUP, x87, vectors, variadic rules, platform-specific coercions, hidden parameters, register exhaustion/spills, stack alignment and final call/return sequences are not implemented. These are ABI planning primitives, not full ABI conformance.

## 5. ELF64/PE32+ object writer, linker and loader

Source: `selfhost/object_pipeline_contract.rpr`.

The object request requires explicit target identity, matching format, architecture-specific machine identifier (ELF x86_64=62, ELF AArch64=183, PE/COFF AMD64=34404), declared process ABI, section and symbol metadata. Link requests reject mixed targets and unverified object inputs. Loader requests require a linked artifact for the exact target and an independent integrity-verification result.

**Status: planned.** The `object_write_elf64`, `object_write_pe32_plus`, `link_executable` and `load_executable` entrypoints intentionally return stable diagnostics instead of placeholder bytes or unsafe execution. ELF headers/sections/symbols/relocations, PE/COFF sections and relocations, symbol resolution, relocation application, executable serialization, import resolution, memory mapping and entrypoint transfer do not yet exist.

## 6. Real target-runtime checks

Workflow: `.github/workflows/typed-compiler-pipeline.yml`.

The workflow runs the Reaper-source conformance modules, then compiles `examples/native_target_runtime_smoke.rpr` through the existing scalar C17 AOT backend and executes the resulting host binary on Linux, macOS and Windows runners. The native source is Reaper; Python is only the repository's existing CLI/reference runner and process harness.

**Boundary:** this is real host-native scalar execution. It does not prove the new typed aggregate ABI classifier, generated ELF/PE artifacts, cross-target execution, DAK runtime compatibility, or cross-compilation to a different target. Those require the corresponding writer/linker/runtime implementation and target-native test fixtures.

## Acceptance commands

```sh
python -m reaper selfhost/typed_ir_tests.rpr
python -m reaper selfhost/generic_types_tests.rpr
python -m reaper selfhost/typed_lowering_tests.rpr
python -m reaper selfhost/native_abi_tests.rpr
python -m reaper selfhost/object_pipeline_tests.rpr
python -m reaper --check examples/native_target_runtime_smoke.rpr
python -m reaper examples/native_target_runtime_smoke.rpr --native build/native-target-smoke
./build/native-target-smoke
```

The dedicated workflow is the acceptance gate; a local source edit or a queued workflow is not a passing result.
