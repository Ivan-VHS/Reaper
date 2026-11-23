# Native compiler: complete front end and DuckOS scalar backend

## Implemented source path

The C17 compiler now has a connected whole-program path for a deliberately bounded scalar subset:

~~~text
.rpr source
  -> UTF-8-aware lexer
  -> expression and statement parser
  -> owned program AST
  -> HIR name, scope, mutability and type checks
  -> MIR functions and control-flow graph
  -> LIR virtual registers and local stack slots
  -> DuckOS DABI64 v1 GNU assembly
  -> ELF64 relocatable object with DuckOS ABI identity
~~~

The AST accepts declarations, immutable and mutable bindings, reassignment, craft functions and parameters, blocks, yield/emit, when/otherwise, loop while, each, lists, calls, indexes and the :: pipeline. HIR resolves names and checks lexical scopes, mutability, function arity and basic types. MIR builds function and control-flow representations. LIR assigns virtual registers, parameter maps and local slots.

## First end-to-end DABI64 machine-code subset

The current full-program target compiles:

- signed i64 parameters, locals and return values;
- make, vary and change;
- direct craft calls with checked argument count and tagged i64 values;
- checked signed +, -, *, / operations;
- when/otherwise branches;
- loop while back edges;
- :: pipe calls, with the left value inserted as argument zero.

A full source program is compiled with:

~~~sh
./build/reaper-c --emit-asm --target duckos-dabi64-v1 \
    examples/native/program.rpr -o build/program.s
~~~

A separate end-to-end test assembles and links the result with a test caller. It executes the top-level program and generated craft functions, including nested calls, local variables, the pipeline operator, conditional branches, a while loop, arithmetic overflow and division-by-zero propagation.

The following constructs are parsed and represented by earlier IR stages but are deliberately rejected by the current machine-code backend: emit, each, list/index operations, dynamic calls, captures, strings and collection built-ins. They require a real DuckOS I/O, string and collection runtime. Parsing or LIR representation is not claimed as executable support.

## DuckOS DABI64 v1 contract

DABI64 is a custom x86-64 DuckOS calling convention, not System V.

| Register / property | Contract |
|---|---|
| R10 | pointer to a read-only DuckCallFrame |
| R11 | pointer to a writable DuckCallResult |
| RAX | DuckAbiStatus return value |
| RSP | 32-byte aligned by the caller immediately before CALL |
| Frame/result/argument addresses | 16-byte aligned |

The frame is 48 bytes and carries the magic, major/minor ABI version, byte size, argument count, capture count, flags, reserved fields and argument/capture pointers. DuckValue and DuckCallResult are 16 bytes. V1 supports up to 64 scalar i64 arguments, no captures and zero flags. A generated function writes a typed result only on success.

The ABI header and host-side reference validator live in the separate DuckOS repository:
[DuckOS DABI64 header](https://github.com/Ivan-VHS/DuckOS/blob/feat/dabi64-abi-runtime/include/duckos/abi/dabi64.h) · [DABI64 contract](https://github.com/Ivan-VHS/DuckOS/blob/feat/dabi64-abi-runtime/docs/abi/DABI64.md).

## Produce a DuckOS-marked ELF object

The compiler emits assembly. The host assembler currently creates the relocatable object; the finalizer verifies ELF64/x86-64, checks for the .note.duckos.abi section and sets the DuckOS EI_OSABI marker (0xD5):

~~~sh
python scripts/duckos_assemble.py \
    --cc cc \
    --assembly build/program.s \
    --object build/program.o
~~~

This produces an ELF64 ET_REL object carrying a DuckOS OSABI marker and ABI note. It is not a native ELF object writer or static linker. Relocation policy, linker scripts, kernel loading and executable startup still need to be implemented.

## Build and test

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

The test suite includes program AST parsing, HIR checks, MIR CFG verification, LIR register/slot verification, deterministic assembly, whole-program DABI64 execution and ELF object finalization.

## Current limits and next stages

| Area | Current state |
|---|---|
| Program parser | structural AST for declarations, functions, blocks, expressions and control flow |
| HIR | lexical resolution, scopes, mutability, arity and basic inferred types |
| MIR | function bodies, locals, calls, :: and branch/loop CFG |
| LIR | virtual registers, local slots, parameter maps and verified blocks |
| System V codegen | checked i64 expressions |
| DuckOS DABI64 codegen | scalar program subset: i64 functions/locals/calls, when, while and :: |
| each, collections, indexing and emit | represented by frontend/IR; not yet executable in the target backend |
| ELF object | host assembler plus checked DuckOS ELF metadata finalization |
| DuckOS linker, loader and process runtime | not implemented |
| Kernel, syscalls, scheduler, memory manager and I/O services | not implemented |
| Self-hosting compiler | not implemented |

Next implementation stages are a runtime for i64 and general tagged values, strings and collections, iteration and I/O; explicit ownership/lifetime lowering; target relocations and a static linker; loader/startup integration; then kernel services and a clean-room self-hosting bootstrap.

Python remains the compatibility oracle until differential tests establish equivalent language semantics. The DuckOS DABI64 validator is a host-buildable ABI reference, not evidence of a bootable OS.
