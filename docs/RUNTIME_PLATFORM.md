# Reaper runtime platform additions

Status: implemented in the Python reference runtime; native C17 parity remains in progress.

## Modules and packages

A source module is a UTF-8 .rpr file. Imports resolve relative to the importing file, canonicalize their paths, enforce the .rpr extension, cap the source size at 2 MB and nesting depth at 64, and cache successful exports.

    # math.rpr
    export craft double(value) {
        yield value * 2
    }

    # main.rpr
    import "math.rpr" as math
    emit math["double"](21)

An import without as binds each exported symbol in the current scope. Only names declared with export are visible to importers. An export may be written as export name, export make name := expression, export vary name := expression, or export craft name(...). Circular imports are rejected with the full canonical path chain. The loader does not execute code during graph scanning.

    python -m reaper --module-graph path/to/main.rpr

The graph is emitted as JSON with canonical absolute paths.

## Managed heap and lifetimes

The reference runtime includes an explicit allocation ledger for lists, maps and bytearrays, recursive tracking of nested containers, a configured byte ceiling, mark/sweep collection from runtime roots, and nested LIFO allocation regions.

Built-ins:
- heap_stats() — tracked object count, estimated bytes, ceiling and active region count.
- heap_collect() — collect allocations not reachable from globals, module exports and the active lexical/VM frame.
- region_begin() — open a nested allocation region and return its token.
- region_end(token) — close the topmost region only when its allocations are no longer reachable.

The default heap-accounting ceiling is 64 MiB; configure it with --heap-bytes. Sizes are host-runtime estimates (sys.getsizeof), not a replacement allocator or a promise that Python's process RSS is capped. Python owns physical allocation and final destruction; Reaper controls its own reachability ledger and region contracts in this reference implementation.

## Deterministic resources

Files are opened only through explicit Reaper built-ins. Supported text modes are r, w, a, and exclusive-create x. A handle is owned by the creating interpreter and cannot be used by another manager. Reads and writes enforce mode, invalid/closed handles fail, and the open handle count is bounded (default 64; --open-resources).

    craft save(handle) {
        file_write(handle, "written by Reaper")
    }
    with_file("output.txt", "w", save)

with_file(path, mode, function) closes in a finally path. All still-open file handles are closed when an interpreter run exits, including on runtime errors. File paths are intentionally explicit and are resolved relative to the current source file unless absolute.

## C ABI and Pytyliki

Native loading is opt-in. Both ffi_open(path) and pytyliki_open(path) fail unless the host enables --allow-native-ffi. The generic C ABI binder supports void, signed/unsigned 8/16/32/64-bit integers, f32, f64, bool, size_t, and cstr.

    python -m reaper --allow-native-ffi path/to/ffi_program.rpr

The typed Pytyliki adapter matches the public structures and functions in Ivan-VHS/Pytyliki/src/core.h: pl_cpu_profile, pl_run_benchmark, pl_analyze_file, and pl_write_json. It validates status codes and exposes structured Reaper maps. The adapter is an opt-in wrapper, not a bundled Pytyliki binary; build Pytyliki as a shared library separately.

ffi_close(handle) logically invalidates a handle; the interpreter also closes all registered handles at run exit. Python ctypes does not provide a portable cross-platform library-unload contract, so physical unload is left to OS process teardown. Native FFI executes in-process and is not a sandbox. Only load trusted, ABI-compatible libraries.

## Embedded C targets and source review

The reference runtime exposes `embedded_targets()`, `embedded_profile(name)`,
`embedded_toolchain(name)`, `embedded_inspect(source)` and
`embedded_build_plan(target, source, output)`. Seven profiles cover host C11,
AVR ATmega328P, ARM Cortex-M0, RISC-V32 IMAC, MSP430G2553, Xtensa ESP32 and
WebAssembly/WASI. Toolchain discovery uses PATH lookup only. Source inspection
is limited to 1 MiB and reports advisory lexical markers for dynamic allocation,
blocking delays, peripheral-register-oriented code and host I/O.

The build-plan function returns an argv list, not a shell command, and never
starts a compiler. Reaper can also read Pytyliki's additive Embedded C ABI
functions through `pytyliki_embedded_targets(path)` and
`pytyliki_embedded_inspect(source, path)`; these require the existing
`--allow-native-ffi` opt-in and an explicit absolute path. Firmware upload,
register writes, covert injection and firmware execution are not implemented.
See [the Embedded C guide](EMBEDDED_C.md).

## Canonical IR and bytecode VM

reaper.ir.lower(parse(source)) lowers the parsed AST into a stack-based Canonical IR. The verifier checks opcode membership, nested functions and jump-target bounds. reaper.vm.assemble maps IR instructions to stable integer opcodes, and VirtualMachine executes constants, lexical environments, calls, closures, control flow, lists, imports/exports and :: pipelines.

    python -m reaper --engine vm examples/flow.rpr

Tree-walk remains the default compatibility engine. The VM currently belongs to the Python reference runtime. The C17 target still has a smaller integer IR bring-up; this change does not claim native C17 bytecode execution or full C/Python parity.

## Reaper Studio debugger

Studio now supports:
- F9 / Breakpoint button: toggle a breakpoint on the editor's current line.
- Debug: begin in single-step mode.
- Continue / Step / Stop controls.
- Variables tab: visible lexical bindings at the paused statement.
- Call stack tab: active Reaper function frames.

The debugger hook is also available as RuntimeDebugger for embedding. Debugger pauses occur at statement boundaries. The Studio UI uses Tk's nested event loop while paused; it does not add a native C debugger or machine-level stepping.

## Verification

The platform regression tests live in tests/test_runtime_platform.py. Run the Python suite with:

    python -m compileall -q reaper tests
    python -m unittest discover -s tests -v

The existing C17 CMake/CTest suite remains a separate build and validation lane.
