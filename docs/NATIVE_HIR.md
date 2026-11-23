# Native HIR, MIR and LIR status

## Current front-end pipeline

The C17 frontend now separates parsing, semantic analysis and control-flow lowering:

~~~text
.rpr source
  -> UTF-8-aware lexer
  -> expression and statement parser
  -> owned program AST
  -> HIR name/scope/mutability/type checks
  -> MIR functions and control-flow graph
  -> LIR virtual registers and local stack slots
~~~

The program AST models declarations, mutation, functions and parameters, blocks, yield/emit, when/otherwise, each/while loops, lists, calls, indexing and the :: pipeline.

HIR owns a typed copy of the AST and resolves symbols through nested scopes. It checks duplicate declarations, make/vary mutability, change assignments, function and built-in arity, basic numeric/logical/comparison types, boolean conditions, return placement and pipe argument insertion. Its inferred types are unit, i64, f64, bool, string, list, function and unknown. Unknown remains explicit where source declarations do not yet provide enough information.

## MIR — implemented structural and control-flow lowering

MIR represents one generated duck_main entry plus one MIR function per craft. Each function has explicit basic blocks, result values, parameter symbol identities and block terminators.

- when lowers to yes/no/join blocks with explicit branch edges.
- loop while lowers to condition/body/exit blocks with a verified back edge.
- each lowers to iterator-init, iterator-next, iterator-current and loop blocks.
- craft parameters are represented in the function parameter table.
- make, vary and change become local stores; identifier reads become local loads.
- calls carry an explicit callee virtual value and an operand vector.
- :: becomes a pipe-call whose first argument is the left-hand value.
- source HIR node IDs remain attached for diagnostics and future debug information.

MIR verification checks contiguous function/block ownership, required terminators, in-function jump/branch targets, result slots, call targets, local symbol identities and one-to-one block instruction ownership. Per-block instruction order is stored independently from the global instruction array, so nested branches do not depend on accidental memory adjacency.

MIR is currently a target-independent representation. It is not yet emitted as machine code.

## LIR — implemented virtual registers and stack slots

The LIR pass converts MIR values into a target-neutral low-level representation:

- MIR results are explicit virtual registers, with a per-function register count.
- Local symbols, mutable bindings, parameters and iteration variables receive stable per-function stack slots.
- Function parameters map to their stack slots through a separate parameter-slot table.
- Calls and pipe calls keep explicit argument vectors.
- Basic blocks and their branch/jump/return terminators remain explicit.
- Iterator/list/index instructions remain named operations until a runtime-aware target pass lowers them.

The LIR verifier checks function/block ownership, stack-slot identities, parameter maps, vreg ranges, argument vectors, terminators and instruction ownership. It is a verified low-level boundary, not register allocation or machine code.

## Current machine-code boundary

The CLI now connects the full program front end to the DABI64 LIR backend:

~~~sh
./build/reaper-c --emit-asm --target duckos-dabi64-v1 \
    examples/native/program.rpr -o build/program.s
~~~

The pipeline is source → program AST → HIR → MIR → LIR → target-specific GNU assembly. The current scalar DABI64 backend emits:

- one duck_program entry and one duck_fn_N symbol per craft function;
- i64 parameters and local stack slots for make, vary and change;
- direct craft calls with checked argument counts and tagged i64 values;
- checked signed arithmetic and division;
- when/otherwise control-flow blocks and loop while back edges;
- :: as an explicit pipe call whose left value becomes argument zero;
- source-independent deterministic labels and a DuckOS ABI ELF note.

The end-to-end test assembles and links this generated code with a host harness. It calls the generated entry and functions using R10/R11 and verifies locals, nested calls, branching, a while loop, the flow operator, arithmetic overflow and division-by-zero propagation.

The scalar backend deliberately rejects emit, each, list/index operations, dynamic calls, captures and collection built-ins. MIR/LIR can represent some of those operations, but a representation is not a runtime implementation. The next compiler work is the DuckOS string/list/iterator and I/O runtime, then ownership and effect-aware lowering.

## DuckOS DABI64 v1

DABI64 is a custom x86-64 DuckOS calling convention, not System V. Each externally visible entry receives R10 = DuckCallFrame pointer and R11 = DuckCallResult pointer; RAX returns a DuckAbiStatus. The caller aligns RSP to 32 bytes before CALL. Frame, result and non-empty argument arrays are 16-byte aligned.

The stable 48-byte frame and 16-byte tagged value layouts, status codes, versioning and reference validator are defined in the companion repository:

- DuckOS DABI64 header: https://github.com/Ivan-VHS/DuckOS/tree/feat/dabi64-abi-runtime/include/duckos/abi
- DABI64 contract: https://github.com/Ivan-VHS/DuckOS/blob/feat/dabi64-abi-runtime/docs/abi/DABI64.md

The DuckOS repository now has a host-buildable frame validator and typed result helpers. This is a reference ABI runtime component, not a kernel or a bootable operating system.

## Object files and remaining OS boundary

Reaper emits GNU assembly. The scripts/duckos_assemble.py helper asks the configured host assembler to create an ELF64 x86-64 ET_REL object, verifies the DABI64 note, and sets ELF EI_OSABI to the DuckOS value 0xD5. This is a reproducible assembler/finalization stage, not a hand-written ELF object writer or a DuckOS static linker.

DuckOS still needs a kernel syscall dispatcher, ELF loader, process startup path, scheduler, address-space validation, allocator, I/O services and collection runtime. None of those should be marked complete until a booted or emulator-run DuckOS image executes a linked DABI64 program through those OS services.

## Acceptance rule

A construct is fully natively compiled only after AST representation, HIR semantics, MIR/LIR lowering, target code generation, object/linker integration and executable tests all exist. Parser or IR support alone is not whole-program compilation.
