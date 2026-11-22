# Native compiler: program front end and expression backends

## Implemented front end

The C17 native parser builds a complete structural AST for declarations, mutable variables, functions and parameters, blocks, yield/emit, when/otherwise, each, loop while, lists, calls, indexing and the :: pipeline.

The HIR semantic pass resolves lexical names and nested scopes, enforces immutable make versus mutable vary, checks change assignments, function-call arity, built-in call arity and basic inferred types. It also checks boolean conditions, yield placement and the language's value-insertion semantics for ::.

This is structural parsing and semantic validation. It does not yet mean that every parsed program is lowered to machine code.

## Current machine-code slice

The currently executable code-generation path remains a checked signed-i64 expression subset:

~~~text
.rpr integer expression -> Pratt AST -> verified i64 IR -> target assembly
~~~

Supported operations are integer literals, parentheses, unary signs and binary +, -, * and /. Overflow, division by zero and INT64_MIN / -1 are explicit failures.

## Build and test

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

The test set now includes complete-program AST parsing and HIR checks for name resolution, local scope, mutability, function arity, built-ins, :: and Russian МОСТ aliases.

## Emit System V assembly

~~~sh
./build/reaper-c --emit-asm examples/native/arithmetic.rpr -o build/arithmetic.s
cc -c build/arithmetic.s -o build/arithmetic.o
~~~

This emits GNU assembler for x86-64 System V ELF. The assembly exports int reaper_program(int64_t *result). The host assembler still creates the object file.

## Emit a DuckOS DABI64 expression

~~~sh
./build/reaper-c --emit-asm --target duckos-dabi64-v1 examples/native/arithmetic.rpr -o build/duck-program.s
~~~

DABI64 v1 uses a separate x86-64 function contract: R10 is the read-only DuckCallFrame pointer, R11 is the writable DuckCallResult pointer and RAX returns DuckAbiStatus. The generated entry validates the frame magic/version/size, rejects arguments/captures not yet supported by this expression entry, checks flags and alignment, writes the typed i64 result only on success and emits .note.duckos.abi.

The ABI data layout and C frame validators are in the DuckOS repository. This backend does not silently fall back to System V.

## Current limits and next stages

| Area | Current state |
|---|---|
| Program parser | implemented for the listed structural constructs |
| HIR | lexical scope, mutability, name and basic type/arity checks |
| MIR | not yet implemented; CFG lowering is next |
| LIR | bounded i64 expression IR only |
| System V codegen | i64 expressions |
| DuckOS DABI64 codegen | no-argument i64 expression entry |
| Object writer/linker | external assembler/linker; no native ELF writer or DuckOS linker |
| DuckOS loader/kernel/runtime | not implemented |

Next: verified MIR functions/CFG, calls and local slots; general LIR; DABI64 call-frame generation for parameterized functions; object relocation writing; DuckOS static linking, loading, startup, syscall dispatch and runtime primitives.

Python remains the compatibility oracle until differential tests establish parity.
