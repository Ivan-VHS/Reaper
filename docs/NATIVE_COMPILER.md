# Reaper Native AOT Compiler

**Author and project maintainer:** Ivan-VHS  
**Status:** experimental, usable scalar AOT slice  
**Source language:** Reaper (.rpr)  
**Target:** C17, then the host platform's GCC- or Clang-compatible toolchain

## Purpose

The reference interpreter remains the compatibility definition for the full Reaper language. The Native AOT path adds a separate, statically checked route for programs that fit a deliberately narrow scalar subset:

\`\`\`text
.rpr source
    -> existing Reaper lexer and parser
    -> source-located semantic and type checks
    -> deterministic C17 source
    -> local C compiler and linker
    -> host executable
\`\`\`

This is a compiler bridge, not a claim that the partial C17 expression IR has become a complete native runtime. It does not write ELF/PE/Mach-O files directly, implement DABI64, or replace the Python interpreter. The operating-system C toolchain owns target object generation and linking.

## Quick start

Emit inspectable C17 without invoking a compiler:

\`\`\`sh
python -m reaper examples/native_scalar.rpr --emit-c build/native_scalar.c
\`\`\`

Build a native executable:

\`\`\`sh
python -m reaper examples/native_scalar.rpr --native build/native_scalar
./build/native_scalar
\`\`\`

On Windows, use an executable name such as build/native_scalar.exe. A GCC- or Clang-compatible compiler named cc, clang, or gcc must be available on PATH. Set the CC environment variable or pass --cc to select the compiler. Use --optimization 0, 1, 2, 3, or s to select the optimization level. The special path - writes generated C17 to standard output.

The compiler is launched with an argument vector, never through a shell. The generated temporary C file is stored in a private temporary directory and removed after the build. The requested output path is explicit; the source file cannot be used as the output path. Builds happen beside the destination, then replace the target only after a successful compile, preserving an existing executable if compilation fails.

## Supported source subset

| Feature | Native AOT behavior |
|---|---|
| make / vary | Lexically scoped immutable/mutable bindings |
| change | Assignment to a previously declared vary binding |
| craft | Top-level functions with integer parameters; direct recursion is bounded; functions cannot emit or mutate globals |
| yield | Integer result on every control-flow path |
| emit | Integer, boolean, or string output at top level |
| when / otherwise | Conditional blocks |
| loop while | Bounded while loop |
| Expressions | +, -, *, //, %, **, comparisons, and, or, not |
| Strings | String literals and bindings; equality and output only |
| Integers | Checked signed 64-bit arithmetic; floor division and modulo follow Reaper semantics, while overflow and division by zero fail at runtime |
| Diagnostics | Unknown names, duplicate bindings, immutable assignment, bad arity and unsupported types are rejected before C generation |

Boolean values are represented as int64_t at the C ABI boundary. Function arguments and results are integers. Every function path must yield a value. Native functions cannot write output or mutate global bindings, keeping calls side-effect free. The generated runtime enforces a one-million-step limit and a 256-frame call-depth limit.

## Explicit native-backend limits

This release does not natively compile each, lists, indexing, :: collection pipelines, ++ concatenation, decimal numbers, nothing, imports/exports, nested functions, closures, dynamic dispatch, asynchronous execution, effects, modules, or arbitrary FFI calls. A program using one of these features receives a source-located native-compiler diagnostic. Run it with the reference interpreter or VM instead:

\`\`\`sh
python -m reaper program.rpr
python -m reaper --engine vm program.rpr
\`\`\`

The backend does not infer that an unsupported construct is safe, and it does not silently route an unsupported expression through Python at runtime. Native programs use only the generated scalar runtime and standard C library output. There is no file, network, process, or hardware API in this subset.

## Safety and reproducibility

- Compilation validates names, mutability, function arity and the supported scalar types before writing output.
- C source generation is deterministic for the same parsed AST and compiler version.
- Arithmetic helpers detect signed overflow, division by zero and invalid exponents rather than relying on C signed-overflow behavior.
- Floor division and modulo use the same sign convention as the Reaper reference runtime.
- The host compiler runs as a subprocess with an explicit argument list and a build timeout.
- No shell command, plugin, FFI library or external process can be invoked by a Reaper source program through this backend.
- The output executable is for the host target selected by the installed C compiler. Cross-compilation and reproducible binary toolchain pinning are separate work.

## Development gates

1. Keep the Python parser/runtime as the semantics oracle until differential tests cover the whole language.
2. Add a new construct only with a type rule, a defined runtime behavior, a negative test and a native execution test.
3. Extend the source map before introducing optimization passes so C diagnostics can be mapped back to .rpr locations.
4. Keep generated C inspectable through --emit-c.
5. Do not describe the backend as a direct ELF linker, a full native interpreter, or self-hosting. Those milestones require their own implementation and acceptance tests.

The next compiler milestones are typed collection lowering, explicit runtime-call contracts, ownership and deterministic drop, a versioned canonical native IR, and a direct object/ELF backend. Each remains separate from this first AOT slice until its conformance tests pass.


## Native IR scalar extension — checked u32

The C17 IR verifier/executor now has a distinct u32 subset: bounded constants, typed add/subtract/multiply/divide, and explicit failure for overflow, underflow and division by zero. This is a lower-level IR primitive, not a new source-language feature.

The current .rpr parser, Python Canonical IR/VM and C17 AOT lowering do not yet emit or execute source-level u32 operations. The AOT compiler remains the limited scalar subset documented above; no direct ELF writer, DABI64 backend or freestanding runtime is implied. The next gate is to connect the type through the source AST, canonical IR and AOT lowering with differential boundary tests.
