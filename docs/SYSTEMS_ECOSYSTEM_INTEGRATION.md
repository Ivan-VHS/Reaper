# Systems ecosystem integration layer

**Status:** registry, validation, project filtering and PATH-only toolchain discovery are implemented. Per-ecosystem compilers, assemblers, simulators, virtual machines and code generators are not bundled by this layer.

## Coverage

The canonical registry is `reaper/systems_ecosystems.json` and contains 40 ordered entries:

| Category | Targets | Count |
|---|---|---:|
| CPU / MCU instruction sets | x86, ARM, RISC-V, MIPS, AVR, 6502, Z80 | 7 |
| Systems languages | C, C++, Rust, Zig, D, Nim, Ada, Modula-2, Oberon | 9 |
| Hardware description | Verilog, SystemVerilog, VHDL, Chisel, Bluespec | 5 |
| VM / bytecode / IR | WebAssembly, LLVM IR, JVM, Dalvik, LuaJIT, Forth, PostScript, BCPL, BLISS | 9 |
| Specialized / graphics / GPU | Brainfuck, FALSE, Befunge, Malbolge, Piet, Whitespace, GLSL, HLSL, SPIR-V, PTX | 10 |

Each entry has a stable ID, category, family, model, applicable standard/version note, toolchain command candidates, capability tags and a short semantic boundary. The older 66-slot systems-language catalogue and 14-slot architecture matrix remain intact; this registry is a distinct integration view and does not renumber either catalogue.

## CLI

```sh
# Inspect all 40 records
python -m reaper --systems-ecosystems

# Narrow to one family
python -m reaper --ecosystem-category isa
python -m reaper --ecosystem-category hdl
python -m reaper --ecosystem-category vm-bytecode

# Rank the targets against an existing project profile
python -m reaper --ecosystem-profile reaper
python -m reaper --ecosystem-profile pytyliki
python -m reaper --ecosystem-profile oplague

# Inspect a single named target or canonical ID
python -m reaper --ecosystem "RISC-V"
python -m reaper --ecosystem gpu-ptx --ecosystems-json

# Discover candidate toolchain executables
python -m reaper --available-ecosystems
python -m reaper --ecosystem-category isa --available-ecosystems

# Validate the packaged registry
python -m reaper.systems_ecosystems --verify
```

The package API exposes `load_matrix`, `validate_matrix`, `select_ecosystems`, `find_toolchains` and `describe_toolchains`. The lookup callback is injectable so tests do not depend on the host machine's installed compilers.

## Integration boundaries

The word "available" means only that at least one configured executable name resolves through the current process PATH. Reaper does not run that program, ask it for a version, compile a probe, link an object, load a runtime, or access hardware during discovery. A matching command is not proof of version compatibility, correct ABI, complete feature support or a working backend.

This registry does not claim to embed seven processor emulators, nine foreign compilers, five HDL simulators, nine foreign VMs or ten esoteric/GPU compilers. The implemented Reaper execution path remains its own Python-reference Canonical IR/bytecode VM. The native C17 path remains the narrow verified integer IR and lowering slice documented in the main architecture guide. The existing opt-in C ABI bridge and Embedded C workflow keep their current contracts.

### Required adapter contract for future backends

A real adapter for any entry must be delivered independently with:

1. A versioned target descriptor: architecture variant, extensions, word size, endianness, ABI, object format and calling convention where applicable.
2. A typed input contract: accepted source/IR dialect and version; unsupported constructs must be diagnosed, never silently dropped.
3. A deterministic compile/assemble/validate pipeline with argument arrays (not shell-concatenated commands), explicit working directory, bounded output and cancellation.
4. Structured diagnostics mapped to source spans and stable error codes.
5. A capability and effect boundary covering filesystem, process execution, dynamic loading, network, device and hardware access.
6. Golden fixtures, negative tests, cross-version tests and CI evidence for each supported target profile.
7. A support declaration distinguishing parser, verifier, assembler, interpreter, simulator, linker and code generator. These stages are not interchangeable.

ISA variants must not be conflated: x86 mode/extensions, Arm execution profile, RISC-V extension/ABI set, MIPS endian/ABI, AVR device family, 6502 variant and Z80 opcode extensions change the target contract. Similarly, HDL versions, shader stage/profile, SPIR-V environment, PTX ISA version and VM/class-file versions must be explicit.

## Verification

The Python unit tests validate all 40 source positions, category counts, unique IDs, profile filtering, exact lookup, injected PATH discovery, JSON output and CLI routing. CTest registers the same suite as `systems-ecosystem-matrix`.

```sh
python -m unittest discover -s tests -p test_systems_ecosystems.py -v
python -m reaper.systems_ecosystems --verify
```

A passing catalogue test verifies the integration registry only. It is not a compiler conformance test for the listed ecosystems.
