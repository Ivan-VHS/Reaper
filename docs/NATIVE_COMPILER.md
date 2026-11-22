# Native compiler: complete front end and expression backends

## Implemented native stages

The C17 path now has distinct frontend and lowering stages:

1. **Program AST:** declarations, mutable bindings, functions/parameters, blocks, yield/emit, when/otherwise, each, loop while, lists, calls, indexes and the :: pipeline.
2. **HIR:** lexical name resolution, nested scopes, mutability, function/builtin arity and basic inferred type checking.
3. **MIR:** generated duck_main and craft functions, locals, explicit calls/pipe-calls, when branches, while back edges and each iterator control flow.
4. **LIR:** explicit virtual registers, per-function local stack slots, parameter-slot mapping, call argument vectors and verified low-level blocks/terminators.

MIR and LIR are checked, target-neutral representations. They are not yet connected to a general machine-code emitter.

## Current executable machine-code subset

The current target emitters still consume the original checked signed-i64 expression IR:

~~~text
.rpr integer expression -> Pratt AST -> checked i64 IR -> target assembly
~~~

Supported operations are integer literals, parentheses, unary signs and binary +, -, * and /. Overflow, division by zero and INT64_MIN / -1 are explicit failures.

This means full-program declarations and control flow are parsed and lowered through LIR, but are not yet compiled to machine code. That distinction is deliberate and documented in [Native HIR/MIR/LIR status](NATIVE_HIR.md).

## Build and test

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

The native test set includes program AST parsing, HIR resolution/type checks, MIR CFG construction/verification, LIR virtual-register/stack-slot validation and end-to-end expression backends.

## Emit a System V expression

~~~sh
./build/reaper-c --emit-asm examples/native/arithmetic.rpr -o build/arithmetic.s
cc -c build/arithmetic.s -o build/arithmetic.o
~~~

The assembly exports int reaper_program(int64_t *result). The host assembler/linker creates the object; Reaper does not yet write ELF relocation records or link an executable.

## Emit a DuckOS DABI64 expression

~~~sh
./build/reaper-c --emit-asm --target duckos-dabi64-v1 examples/native/arithmetic.rpr -o build/duck-program.s
~~~

DABI64 v1 uses its own x86-64 function convention: R10 is a read-only DuckCallFrame pointer, R11 is a writable DuckCallResult pointer and RAX returns DuckAbiStatus. The generated entry validates the frame magic/version/size, no-argument entry shape, flags and result alignment; it writes a typed i64 result only on success and emits .note.duckos.abi.

The ABI data layout and C frame validators are in the separate DuckOS repository. This backend does not silently fall back to System V.

## Current limits and next stages

| Area | Current state |
|---|---|
| Program parser | complete structural AST for the listed constructs |
| HIR | lexical scope, names, mutability, call arity and basic type checks |
| MIR | functions, local access, calls, ::, when/while/each CFG and verifier |
| LIR | virtual registers, local stack slots, parameter maps, calls and verified blocks |
| System V codegen | checked i64 expressions only |
| DuckOS DABI64 codegen | no-argument checked i64 expression entry only |
| MIR/LIR machine-code backend | not yet implemented |
| Object writer/linker | external assembler/linker; no native ELF writer or DuckOS linker |
| DuckOS loader/kernel/runtime | ABI layout/validators only; OS components are not implemented |

Next: target-specific lowering from LIR, full DABI64 function/call-frame generation, runtime support for collections/iteration/I/O, relocatable ELF emission, DuckOS linking/loading/startup and kernel syscall dispatch.

Python remains the compatibility oracle until differential tests establish equivalent semantics.
