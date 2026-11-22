# Native compiler: first executable target

## What the backend does today

The C17 track now has an end-to-end compiler path for a deliberately small, fully checked language subset:

.rpr expression → native lexer with UTF-8-aware source positions → Pratt parser → owned AST → typed i64 IR → x86-64 assembly.

The backend accepts signed 64-bit integer literals, parentheses, unary + and -, and binary +, -, * and /. Division uses the IR's signed integer contract and truncates toward zero. Every other expression form is rejected with a diagnostic; the compiler does not guess a conversion or call back into Python.

The native compiler is an expression compiler at this stage. It does not yet compile declarations, local variables, functions, modules, strings, arrays, control flow or the :: pipeline into machine code.

## Build and emit

Build the C17 tools:

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

Compile the checked example to GNU assembler:

~~~sh
./build/reaper-c --emit-asm examples/native/arithmetic.rpr -o build/arithmetic.s
~~~

The generated file exports one C-callable function:

~~~c
int reaper_program(int64_t *result);
~~~

Assemble the file on Linux x86-64 with the system C toolchain:

~~~sh
cc -c build/arithmetic.s -o build/arithmetic.o
~~~

The generated object can be linked into a host program that declares and calls reaper_program. The native smoke test in CTest does exactly that for success, overflow, division-by-zero and a null result pointer.

## ABI and runtime contract

This first backend targets **x86-64 System V ELF** and emits GNU assembler syntax. It is not a generic x86-64, Windows x64, Mach-O, AArch64 or DuckOS ABI backend.

The generated function returns a ReaperCodegenStatus value:

| Return code | Meaning |
|---:|---|
| 0 | success; result contains the expression value |
| 1 | signed i64 overflow |
| 2 | integer division by zero |
| 3 | null result pointer |

The output pointer is checked before it is used. The result is stored only after the entire IR program reaches its final RETURN; failure leaves the caller's result unchanged. Addition, subtraction and multiplication branch on the processor's signed-overflow flag. Division checks both zero and the INT64_MIN / -1 overflow case before executing idiv.

The generated function has no allocator, runtime-library or operating-system calls. It keeps its temporary i64 values in a bounded stack frame. The verifier requires topologically ordered IR, matching operand types and exactly one final RETURN; the backend caps a module at 4096 IR nodes.

## What this is not

- It is not full Reaper language support or Python-runtime parity.
- It does not yet produce object files, executables, debug information or relocatable libraries directly; GNU assembler and a linker remain external tools.
- It does not provide a kernel ABI, system-call layer, driver ABI, process runtime, allocator, garbage collector or OS sandbox.
- It does not establish self-hosting. The native frontend is still C17, while the Reaper-written lexer and partial Pratt parser remain bootstrap components.

These boundaries are intentional. The first milestone is a small compiler path with observable semantics and an executable test, not a wide command surface whose features are only registered.

## Next compiler milestones

1. Bring the Reaper-written lexer to Unicode and error-location parity with the reference lexer.
2. Complete declarations, blocks and statement parsing in Reaper source; freeze a versioned canonical AST.
3. Add a semantic pass with explicit types, immutable bindings by default, explicit mutation and effect boundaries.
4. Extend the IR with functions, locals, branches, calls and source maps while preserving verification and resource budgets.
5. Add target-specific object emission, debug information and a linker/runtime contract for DuckOS.
6. Rebuild the frontend and compiler stages from Reaper source and prove clean-room, reproducible bootstrap parity.

Python remains the compatibility oracle until differential tests demonstrate that a native stage preserves the language's actual semantics.
