# Native IR execution and code generation

| Area | Contract |
|---|---|
| IR | typed nodes with stable indices and topological references |
| Integer operations | checked signed i64 add, subtract, multiply and divide |
| Division | truncation toward zero; zero and INT64_MIN / -1 are explicit failures |
| Lowering | integer literals, unary + / -, binary + / - / * / / |
| Verification | operand type checks, earlier-node references and one final RETURN at codegen |
| Optimization | bounded, deterministic fixed-point constant folding |
| Backend | x86-64 System V ELF GNU assembler; no runtime calls |
| Errors | explicit diagnostics; no silent overflow or division-by-zero behavior |
| Status | partial expression compiler; not a full native interpreter or program compiler |

## Execute verified IR in the C17 core

The IR evaluator uses caller-owned scratch storage and writes the result only after the final RETURN succeeds:

~~~c
int64_t values[16] = {0};
int64_t result = 0;
ReaperIrError error;

if (!reaper_ir_execute_i64(&module, values, 16, &result, &error)) {
    /* error.message describes the rejected operation */
}
~~~

## Emit native assembly

The CLI pipeline is:

~~~sh
./build/reaper-c --emit-asm examples/native/arithmetic.rpr -o build/arithmetic.s
cc -c build/arithmetic.s -o build/arithmetic.o
~~~

The assembly exports int reaper_program(int64_t *result). Return codes are 0 for success, 1 for signed overflow, 2 for division by zero and 3 for a null output pointer. A failed execution does not modify the output value.

The Linux x86-64 CTest smoke test invokes the compiler, assembles the generated file, links a small C caller and runs normal and failing expressions. Text-generation tests also compare two independent emissions byte-for-byte.

## Compatibility boundary

Python remains the reference for all semantics outside the implemented C17 i64-expression subset. The backend is currently x86-64 System V ELF only. It does not compile declarations or general .rpr programs, emit object files itself, or supply the DuckOS process/runtime ABI.
