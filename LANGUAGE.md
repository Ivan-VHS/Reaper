# Reaper Language — Draft 0.1

Reaper is an independent, text-first, expression-oriented language with an explicit data-flow operator. Version 0.1 is an interpreter with an additive compiler front end; it is not yet a native-code compiler.

## Design rules

1. **Calm surface, visible effects.** Console I/O is explicit through emit, say, and ask. Ordinary expressions do not access files, networks, or clocks.
2. **Immutability by default.** make binds an immutable name. vary explicitly permits reassignment; change is the reassignment statement.
3. **Flow as composition.** value ~> transform(args) passes the value on the left as the first argument to the next call. Flow chains associate left to right.
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
    ~> map(double)
    ~> keep(is_large)
    ~> fold(0, add)

emit "result = " ++ text(result)
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

1. ~> — flow composition.
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
| keep(list, predicate) | Keep items whose predicate is truthy |
| fold(list, initial, function) | Reduce values from left to right |
| assert(condition[, message]) | Raise a runtime error when condition is false |

Flow passes the left-hand value as the first argument: values ~> map(double) is equivalent to map(values, double).

## Execution

~~~sh
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --steps 2000000 examples/flow.rpr
python -m reaper --items 50000 --text-length 500000 examples/flow.rpr
~~~

The default limits are 1,000,000 execution steps, 256 nested function calls, 100,000 collection items and 1,000,000 characters produced by text concatenation. The CLI exposes --steps, --items and --text-length; the Python API exposes the same collection and text limits through Interpreter and run().

A quota violation stops execution with a Reaper runtime diagnostic. These limits are resource guardrails, not a security sandbox; do not run untrusted programs under the assumption that the interpreter isolates them from the host process.

Python 3.10+ is required. The interpreter uses only the Python standard library.

## Compiler and runtime foundations

Install the package in editable mode, then use the additional compiler front end:

~~~sh
python -m pip install -e .
reaperc examples/flow.rpr
reaperc examples/flow.rpr --optimize
~~~

The reaperc command parses the same .rpr source, runs a conservative static checker, lowers the syntax tree to source-mapped Quarry IR, verifies IR structure and emits canonical JSON with source and IR SHA-256 digests. The --optimize option enables side-effect-free literal constant folding. Invalid types stop compilation by default; --allow-type-errors emits IR with diagnostics for analysis. This is a portable IR front end, not a native-code, bytecode or JIT backend.

Python host APIs provide the first runtime foundations:

- reaper.resources: bounded logical regions, move-invalidated handles, scoped borrows and epoch-delayed reclamation. Python still owns the actual objects; this is not a deterministic native allocator.
- reaper.concurrency: typed bounded channels, asynchronous actors, backpressure and scoped actor shutdown with restart supervision.
- reaper.security: process-local HMAC capability tokens, revocation and context-scoped permission checks. This is an API boundary, not an operating-system sandbox.
- reaper.checkpoint: checksummed atomic JSON snapshots and copy-on-write transactions for application state. It does not serialize a live Python stack or transparently resume an executing actor.
- reaper.profiling: call counts, timing records and hot-function detection. It does not generate machine code or perform JIT compilation.
- reaper.interop: a limited scalar C prototype reader, capability-gated ctypes loading, foreign-handle lifetime and an adapter registry. The only included adapter is Python; JavaScript, JVM, .NET and WebAssembly bridges are not shipped.

See docs/PLATFORM_ARCHITECTURE.md for the independent subsystem vocabulary, staged roadmap, implementation evidence and remaining acceptance gates.

## Implementation boundary

Implemented: lexer, parser, AST interpreter, lexical closures, lists, functions, flow composition, console I/O, source diagnostics and execution quotas; plus the additive typed IR front end, conservative static checks, constant folding, explicit logical regions, actor/channel runtime, capability API, application-state snapshots, profiler and limited C ABI/adapter primitives.

Not implemented: native AOT/JIT/SIMD, a self-hosting compiler, full hygienic macros, process-level checkpoint migration, distributed scheduling, a full C preprocessor, JS/JVM/.NET/WASM bridges, a debugger, a package manager or an independent security audit. No roadmap item is considered complete merely because a name or interface exists.
