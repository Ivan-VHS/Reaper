# REAPER 66 low-level reference ecosystem bridge

## Purpose and boundary

This registry preserves the supplied 66 positions across machine assembly, systems languages, virtual machines, hardware description, GPU/parallel computing and esoteric machines. It complements the existing 66-position systems-language capability matrix; it does not replace or renumber that catalogue.

The entries are intentionally heterogeneous. Some are source languages, some are instruction-set assembly families, bytecode formats, compiler IRs, hardware DSLs, subsets or dialects. The registry preserves the supplied positions rather than pretending that all 66 have interchangeable semantics or need separate Reaper frontends.

**Current implementation status: catalogued-only.** Reaper can validate the registry, group entries by capability profile and discover candidate executable names on PATH. It does not invoke external tools, install toolchains, translate foreign source, synthesize hardware, launch GPU kernels or claim 66 working compiler backends.

## CLI

```sh
# Validate the machine-readable registry
reaper compat verify

# Browse the complete 66-entry catalogue
reaper compat list

# Filter by Reaper capability needs
reaper compat list --profile reaper
reaper compat list --profile embedded
reaper compat list --profile gpu
reaper compat list --profile hdl
reaper compat list --profile vm
reaper compat list --profile stack
reaper compat list --profile esoteric

# Inspect one entry by canonical name or alias
reaper compat show "RISC-V"
reaper compat show "LLVM IR" --json
reaper compat show "CamelForth"

# Restrict the results to toolchain candidates visible on PATH
reaper compat list --profile gpu --available-only
```

`--available-only` means that at least one configured executable name was found by PATH lookup. It does not verify the executable version, invoke the tool, compile code, detect a physical device, prove target support or certify ABI compatibility. An entry with no known command candidates is reported as `not-probed`, not as unavailable.

## Reference groups

| Positions | Group | Reaper integration boundary |
|---|---|---|
| 01–10 | x86, AArch64, RISC-V, MIPS, AVR, 6502, Z80, m68k, PowerPC, SPARC assembly | Target-specific instruction selection, assembler syntax, register allocation, ABI and object format |
| 11–12 | WAT and LLVM IR | Portable virtual ISA and typed compiler-interchange representation |
| 13–24 | C, C++, Rust, Zig, D, Nim, Ada, SPARK, Modula-2, Oberon, BCPL, BLISS | Systems-language semantics, ownership/contracts, compile-time facilities and explicit C ABI/FFI |
| 25–36 | Forth, Factor, PostScript, Lua/LuaJIT, JVM/Jasmin, Dalvik/Smali, Erlang, Elixir, Smalltalk, Objective-C, Swift, Vala | Stack/register VM models, managed runtimes, actors, image runtimes and native interop |
| 37–46 | Verilog, SystemVerilog, VHDL, Chisel, Bluespec, SpinalHDL, Amaranth, Silice, MyHDL, FIRRTL | A distinct hardware pipeline: elaboration, RTL, simulation, verification, synthesis and timing |
| 47–56 | GLSL, HLSL, SPIR-V, CUDA C++, PTX, OpenCL C, Metal, WGSL, ISPC, Chapel | GPU shader/compute IR, CPU SIMD/SPMD and parallel execution models |
| 57–66 | Brainfuck, FALSE, Befunge-98, Whitespace, Malbolge, Piet, Ook!, HQ9+, Subleq, Forth-83/CamelForth | Small-machine and interpreter conformance fixtures; not general-purpose native backends |

The repeated Forth family positions and related dialect/subset entries remain separate source positions where the supplied list makes them separate. SPARK is treated as an Ada verification subset, FIRRTL as a hardware compiler IR, and SPIR-V/PTX/LLVM IR as intermediate/virtual instruction formats rather than ordinary high-level source languages.

## Shared REAPER/MOST architecture

The long-term integration model is a shared front end and semantic core, not a source-level mixture of foreign syntaxes:

```text
REAPER frontend ─┐
MOST frontend ───┼─> tokens / AST ─> name + type + effect analysis
Foreign adapters ┘                         │
                                           v
                             ownership / region / ABI checks
                                           │
                                           v
                                  Canonical Semantic IR
                                           │
                                    IR verifier
                                           │
                     ┌─────────────────────┼──────────────────────┐
                     v                     v                      v
                Native targets         WASM targets          Specialized flows
             x86/AArch64/RISC-V          WAT/WASI           HDL / GPU / VM adapters
                     │                     │                      │
                     v                     v                      v
             assembler + linker       host runtime          target toolchain
```

The common semantic core owns language meaning. An adapter may provide syntax ingestion, a foreign ABI boundary, target metadata, bytecode import/export or a separate tool invocation contract. It must not silently alter Reaper types, effects, ownership rules or observable behavior.

### Capability mapping

- **Machine assembly and CPU ISAs:** architecture profiles supply register sets, data layout, calling convention, ABI, relocation/object format and target feature constraints. Inline assembly and raw pointers remain explicit unsafe operations.
- **Systems languages:** C ABI/FFI is the narrow interoperability boundary. Rust/Ada/SPARK contribute reference models for ownership, contracts and proof obligations; Zig/D/Nim contribute compile-time and allocator design references. Their complete syntax and runtime semantics are not imported implicitly.
- **IR and virtual machines:** LLVM IR and WebAssembly are candidates for verified backend interchange. JVM, Dalvik, BEAM, Lua and stack-machine formats require distinct verification and runtime contracts; they are not interchangeable bytecode.
- **HDL:** hardware descriptions lower to circuits, not normal CPU executables. Their acceptance gates must include elaboration, RTL equivalence, simulation, assertions, synthesis and timing reports where applicable.
- **GPU and parallel systems:** GPU code requires explicit device capabilities, memory spaces, synchronization and launch geometry. CPU SIMD and distributed parallelism remain separate execution models.
- **Esoteric machines:** these are useful as compact interpreter, parser, control-flow and resource-limit fixtures. They do not justify expanding the safe systems-language core with arbitrary exotic syntax.

## Adapter maturity levels

| Level | Meaning | Evidence required |
|---|---|---|
| 0 — Catalogued | Entry, role and capability tags are present | Schema validation |
| 1 — Discovered | A candidate executable is visible on PATH | Injected/real PATH lookup; no execution |
| 2 — Validated | Exact toolchain and target version are checked | Reproducible version probe and target metadata |
| 3 — Adapted | An adapter can emit/consume a documented interchange format | Positive and negative adapter tests |
| 4 — Backend implemented | Reaper semantics lower to the target correctly | IR verification, ABI fixtures, differential and target conformance tests |

The current CLI implements Level 0 and the discovery portion of Level 1. Its `adapter_state` deliberately remains `catalogued-only` for all 66 entries. A detected compiler path does not automatically raise this status.

## Delivery order

1. Complete the native semantic core: declarations, types, effects, verified Canonical IR, ownership/region analysis and deterministic diagnostics.
2. Establish a stable interchange contract and verified LLVM IR/WASM output for the supported semantic subset.
3. Add a small native target set first: x86-64, AArch64 and RISC-V, with ABI fixtures and explicit cross-compilation profiles.
4. Extend embedded targets (AVR, 6502 and Z80) only after memory layout, interrupt, linker and freestanding runtime contracts are testable.
5. Build HDL and GPU flows as separate adapters with their own simulation/device/toolchain gates.
6. Add VM import/export adapters only when bytecode verification and host-runtime boundaries are specified.
7. Keep esoteric entries as bounded conformance fixtures, isolated from production code generation.

## Safety and provenance

- Registry data is descriptive and does not execute source code.
- Toolchain discovery uses `shutil.which`; it never runs discovered executables.
- No external source is copied into Reaper by this registry.
- Future adapters must record tool identity, version, licence/provenance, target ABI, invocation arguments and generated artifact hashes.
- External compiler execution must use explicit opt-in, argument arrays (not shell strings), bounded time/output, controlled working directories and documented environment variables.
- Native FFI, assembly, device access, firmware operations and shader dispatch require separate capability gates.
- A registry entry, roadmap row or available executable is not evidence that the feature is implemented or safe.

## Source of truth

- Machine-readable catalogue: `reaper/reference_ecosystems.json`
- Registry validator and PATH-only discovery: `reaper/reference_ecosystems.py`
- Regression tests: `tests/test_reference_ecosystems.py`
- Existing complementary catalogue: `reaper/systems_languages.json`
- Shared compiler and MOST decisions: `docs/REAPER_UNIFIED_ARCHITECTURE.md` and `docs/MOST_LANGUAGE_SPEC.md`
