# Processor backend prototypes v1

**Maturity:** five independently built, bounded prototypes. None is marked target-qualified or hardware-qualified.

## Backend 1 — structured native assembler

Target: RV32I
ABI: ILP32

Input is a caller-owned array of typed instruction records and explicit symbol labels. The backend encodes this supported subset:

- ADDI, ANDI, ORI, XORI, SLTI;
- LUI, AUIPC;
- ADD, SUB, AND, OR, XOR, SLT;
- LW, SW;
- BEQ, BNE, JAL, JALR;
- NOP as ADDI x0,x0,0.

JAL and branch references can create bounded PC-relative relocations. Registers, immediate widths, alignment, instruction count, label count and relocation count are checked. This is a structured instruction encoder, not a textual assembly parser, a complete RV32I implementation or a general macro/preprocessor assembler.

## Backend 2 — native linker

The linker consumes up to eight versioned in-memory RV32I object records with exact target/ABI identity, combines their code words deterministically, checks duplicate and unresolved symbol IDs, and applies JAL20 and BRANCH13 relocations with checked signed range arithmetic.

Output is a bounded flat image with an entry address and symbol table. It is not ELF, PE, Mach-O, a relocatable object writer, a dynamic linker, a loader or a firmware packager. Section permissions, GOT/PLT, TLS, debug/unwind tables and external symbol versioning are out of scope.

## Backend 3 — bounded RV32I emulator

The emulator currently executes the assembler subset, using 32 integer registers, local caller-owned 4 KiB RAM, little-endian 32-bit load/store, a strict instruction/target check, a step cap of one million and a trace capped at 128 records. It halts when PC reaches the linked image's exclusive end; otherwise it reports an illegal instruction, out-of-range memory access or step limit.

It does not implement the full RV32I privileged or unprivileged ISA, compressed instructions, atomics, CSRs, exceptions/interrupts, MMU, caches, devices, MMIO, DMA, timers, multi-hart behavior or real-time timing. Emulator success is not hardware qualification.

## Backend 4 — RTL emitter

A typed, topologically ordered combinational Boolean netlist with at most 32 inputs and 64 gates can be emitted as a small SystemVerilog module. Gate kinds: AND, OR, XOR and NOT. Every gate may reference only primary inputs or earlier gates; invalid cycles/forward references and buffer exhaustion are rejected.

This is a combinational structural emitter only. It does not implement a processor pipeline, clock/reset domains, sequential elements, bus protocols, memories, timing constraints, technology mapping, synthesis, place-and-route or silicon output. A generated SystemVerilog file is not a synthesized or timing-qualified design.

## Backend 5 — bounded formal equivalence

The formal prototype compares two valid combinational Boolean nets with equal input counts and exhaustively checks all input combinations for up to eight input bits. It returns proved, counterexample (with input/output values), or unknown when the request exceeds the supported bound or cannot be admitted.

Proved means equivalence for every input in this finite, explicitly represented combinational model. It is not a proof of sequential behavior, analog properties, a complete processor, compiler correctness or a physical implementation. No external SMT/SAT engine, proof certificate or trusted proof kernel is claimed.

## Build and tests

The CMake graph keeps assembler, linker, emulator, shared logic-net validator, RTL emitter and formal checker as separate static-library targets. Dedicated CTest executables cover:

- instruction encodings and immediate/register rejection;
- link relocations, duplicate and unresolved symbols;
- emulator load/store, register state, trace and step limit;
- SystemVerilog output and output-buffer bounds;
- exhaustive equivalence, counterexamples and the explicit eight-input limit.

The prototypes are C17 and use caller-owned bounded structures. They perform no network access, host scheduling, native process spawning, hardware register access, MMIO mapping, DMA, firmware update, driver installation or device control.

## Maturity promotion

Every backend begins as prototype. Promotion requires a pinned independent toolchain, reviewed target/ABI documentation, positive and negative conformance vectors, deterministic artifacts, malformed-input tests, resource bounds, source/provenance mapping and CI evidence. Target qualification and hardware qualification are separate statuses; neither is inferred from a passing unit test.
