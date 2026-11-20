# Reaper Language — Draft 0.1

Reaper is an independent, text-first, expression-oriented language with an explicit data-flow operator. Version 0.1 is an interpreter, not a native-code compiler. It defines a deliberately small core that can grow behind stable, testable semantics.

## Design rules

1. **Calm surface, visible effects.** Console I/O is explicit through emit, say, and ask. Ordinary expressions do not access files, networks, or clocks.
2. **Immutability by default.** make binds an immutable name. vary explicitly permits reassignment; change is the reassignment statement.
3. **Flow as composition.** value :: transform(args) passes value as the first argument to the next call. Flow chains associate left to right.
4. **Structural composition.** Functions are values and can be passed to map, keep, and fold. No class hierarchy is needed.
5. **Bounded execution.** A configurable step budget and call-depth limit stop runaway programs.
6. **No silent coercion.** Arithmetic is numeric. ++ joins text only. Convert explicitly with text() or number().

## Example

~~~reaper
craft double(value) {
    yield value * 2
}

craft is_large(value) {
    yield value >= 6
}

craft add(total, value) {
    yield total + value
}

make result := [1, 2, 3, 4, 5]
    :: map(double)
    :: keep(is_large)
    :: fold(0, add)

emit "result = " ++ text(result)
~~~

## 666-token symbolic catalogue

Reaper includes a canonical 666-entry symbolic vocabulary over `: ; [ { ] } + = _ - *`. Each reserved lexeme is a unique three-symbol code with no digits. The six groups cover memory, streams, types, arithmetic, metrics and diagnostics. The Python and native C lexers recognize these codes; use `reaper --catalog` or the `token_catalog()`, `token_info()` and `token_is_reserved()` built-ins to inspect them. Vocabulary registration does not imply operation semantics are implemented: reserved operators are rejected by the parser until their contracts are implemented. See [TOKEN_CATALOG](docs/TOKEN_CATALOG.md).

## Modules

Modules are UTF-8 .rpr files resolved relative to the importing file. An import with as binds a module map; an import without an alias binds its explicitly exported names. Access a member with map indexing, for example module["function"](...). Export declarations can mark an existing name or declare a make, vary, or craft binding. Import cycles are rejected and the CLI can inspect the transitive graph without executing code:

~~~sh
python -m reaper --module-graph examples/modules/main.rpr
~~~

## Source format

- Source files use the .rpr extension.
- Newlines separate statements; semicolons are not part of the language.
- Comments begin with # and continue to the end of the line.
- Text literals use double quotes and support \n, \r, \t, \", and \\ escapes.
- Identifiers accept Unicode letters, digits after the first character, and underscores.

## Statements

~~~reaper
make fixed_value := expression
vary changing_value := expression
change changing_value := expression

craft function_name(argument, another) {
    yield expression
}

when condition {
    emit "yes"
} otherwise {
    emit "no"
}

each item in collection {
    emit item
}

loop while condition {
    emit "looping"
}

emit expression
~~~

A function returns nothing when it reaches its end without yield. yield outside a craft function is an error.

## Values and operators

Version 0.1 supports whole numbers, decimal numbers, text, booleans (true / false), nothing, and lists.

Operators, from low to high precedence:

1. :: — flow composition.
2. or.
3. and.
4. ==, !=, <, <=, >, >=.
5. ++ — text concatenation.
6. +, -.
7. *, /, //, %.
8. **.
9. Unary - and not.

Calls use name(arguments); list indexing uses collection[index]. Arithmetic does not implicitly coerce booleans or text. Comparison is defined for two numbers or two text values.

## Standard operations

| Operation | Meaning |
|---|---|
| say(a, ...) | Print values separated by spaces |
| ask(prompt) | Read one line from standard input |
| size(value) | Length of text, list, map, or range |
| text(value) | Convert a value to display text |
| number(value) | Explicit numeric conversion |
| kind(value) | Return nothing, boolean, number, text, list, map, or craft |
| range(stop) / range(start, stop[, step]) | Create an integer range |
| push(list, value) | Return a new list with value appended |
| first(list) / rest(list) | Read the first value / return all but the first |
| sum(list) / sorted(list) | Numeric sum / sorted copy |
| map(list, function) | Transform every item |
| keep(list, predicate) / filter(list, predicate) | Keep items whose predicate is truthy |
| fold(list, initial, function) / reduce(list, initial, function) | Reduce values from left to right |
| sorted(list[, key][, "asc" or "desc"]) / sort_by(list, key[, direction]) | Stable sorting with optional function key and direction |
| chunk(list, width) / take(list, count) / drop(list, count) | Split into bounded blocks or take/drop a prefix |
| flatten(list_of_lists) / unique(list) / reverse(sequence) | One-level flattening, stable de-duplication, reverse |
| split(text, separator) / join(texts, separator) | Split and join strings |
| trim / lower / upper / replace / contains / starts_with / ends_with | UTF-8 string operations |
| assert(condition[, message]) | Raise a runtime error when condition is false |
| file_open(path[, mode]) / file_read(handle) / file_write(handle, text) / file_close(handle) | Explicit UTF-8 file access with owned handles |
| with_file(path, mode, function) | Scoped file access; always closes the handle |
| heap_stats() / heap_collect() | Inspect the tracked heap ledger / collect unreachable tracked containers |
| region_begin() / region_end(token) | Open and close nested LIFO allocation regions |
| ffi_open(path) / ffi_bind(library, symbol, return_type[, argument_types]) / ffi_close(handle) | Opt-in native C ABI calls |
| pytyliki_open(path) / pytyliki_cpu_profile(bridge) / pytyliki_benchmark(bridge, iterations) | Typed Pytyliki C ABI adapter |

Flow passes the left-hand value as the first argument: values :: map(double) is equivalent to map(values, double).

## Execution

~~~sh
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --lint examples/flow.rpr
python -m reaper --repl
python -m reaper --profile examples/flow.rpr
python -m reaper --json --profile examples/flow.rpr
python -m reaper --steps 2000000 examples/flow.rpr
python -m reaper --items 50000 --text-length 500000 examples/flow.rpr
python -m reaper --engine vm examples/flow.rpr
python -m reaper --module-graph examples/modules/main.rpr
python -m reaper --heap-bytes 67108864 --open-resources 64 examples/flow.rpr
~~~

The default limits are 1,000,000 execution steps, 256 nested function calls, 100,000 collection items and 1,000,000 characters produced by text concatenation. The CLI exposes `--steps`, `--items` and `--text-length`; the Python API exposes the same collection and text limits through `Interpreter` and `run()`.

A quota violation stops execution with a Reaper runtime diagnostic. These limits are resource guardrails, not a security sandbox; do not run untrusted programs under the assumption that the interpreter isolates them from the host process.

Python 3.10+ is required. The interpreter uses only the Python standard library.

## Self-hosting status

The bootstrap has started, but Reaper is not yet a self-hosting compiler.

- **Stage 0 (partial):** `selfhost/lexer.rpr` implements an initial lexer in Reaper source and runs on the Python reference interpreter. The current slice covers ASCII identifiers; Unicode identifier parity is still required.
- **Not yet implemented:** a Reaper-written parser/AST builder, semantic analysis, Canonical IR construction, optimizer, native code generator and reproducible stage-0/stage-1 compiler rebuild.

The Python interpreter remains the compatibility oracle. The bootstrap stages and acceptance gates are defined in [SELF_HOSTING_BOOTSTRAP](docs/SELF_HOSTING_BOOTSTRAP.md).

## Runtime platform status

The Python reference runtime now includes .rpr modules with explicit exports and cycle detection, a tracked heap with mark/sweep reachability and LIFO regions, deterministic scoped file handles, opt-in C ABI FFI and a typed Pytyliki adapter, Canonical IR lowering and a selectable bytecode VM. Reaper Studio exposes statement breakpoints, stepping, visible lexical variables and the function call stack. See [RUNTIME_PLATFORM.md](docs/RUNTIME_PLATFORM.md) for contracts and limits.

These are reference-runtime facilities. The heap ledger estimates allocation size and does not replace Python's physical allocator. Native library handles are logically invalidated; physical unload is platform-managed. Native FFI is in-process and not a sandbox. The new bytecode VM is currently Python-based; native C17 bytecode execution is not yet claimed.

## Implementation boundary

Implemented in 0.1: lexer, parser, tree-walk interpreter, lexical closures, lists, functions, flow composition, console I/O, source diagnostics, an execution-step budget, call-depth limits, collection-item limits and text-concatenation limits.

Not implemented yet: static type checking, algebraic effect handlers, semantic-graph storage, native compilation, GPU execution, distributed scheduling, formal verification, package registry, or a complete self-hosting compiler. These are roadmap goals, not current guarantees.

## Orthogonal metric built-ins

Reaper also provides pure numerical helpers: metric_dot, vector_norm (L1/L2/L-infinity), vector_normalize, euclidean_distance, squared_euclidean_distance, manhattan_distance, chebyshev_distance, cosine_similarity, angle_between, vector_projection, vector_centroid, is_orthogonal, quadratic_form, law_of_cosines, de_gua_area, parseval_energy, unit_circle_residual, spherical_hypotenuse, hyperbolic_hypotenuse, minkowski_interval, combine_variances and reciprocal_altitude. All vector arguments are lists of finite numbers. The vector and matrix limits, dimensional checks, geometric domains and statistical assumptions are documented in docs/ORTHOGONAL_METRIC_ENGINE.md. These helpers do not grant host I/O or hardware capabilities.
