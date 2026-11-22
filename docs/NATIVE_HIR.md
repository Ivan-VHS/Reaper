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

The existing target emitters still consume the older verified i64 expression IR. They generate:
- x86-64 System V ELF assembly;
- x86-64 DuckOS DABI64 v1 assembly with the .note.duckos.abi note.

Those backends compile the checked no-argument i64 expression entry only. They do not yet consume general MIR/LIR functions, parameterized calls, local slots or control-flow graphs. The next implementation stage is LIR-to-DABI64 lowering and a runtime contract for collections, iteration, strings, output and failure propagation.

## Object files and DuckOS runtime boundary

Reaper currently emits assembly text; the host assembler/linker creates the test objects. There is no native ELF relocatable-object writer or DuckOS static linker yet.

DuckOS contains a versioned ABI header, frame/result validators and contract tests. The kernel syscall dispatcher, ELF loader, process startup, scheduler and user-space runtime are not implemented yet. A DABI64 host-call test verifies the register/frame contract only; it is not evidence of a bootable operating system.

## Acceptance rule

A construct is fully natively compiled only after AST representation, HIR semantics, MIR/LIR lowering, target code generation, object/linker integration and executable tests all exist. Parser or IR support alone is not whole-program compilation.
