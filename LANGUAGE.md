# Reaper Language — Draft 0.1

Reaper is an independent, text-first, expression-oriented language with an explicit data-flow operator. Version 0.1 is an interpreter, not a native-code compiler. It defines a deliberately small core that can grow behind stable, testable semantics.

## Design rules

1. **Calm surface, visible effects.** Console I/O is explicit through emit, say, and ask. Ordinary expressions do not access files, networks, or clocks.
2. **Immutability by default.** make binds an immutable name. vary explicitly permits reassignment; change is the reassignment statement.
3. **Flow as composition.** value ~> transform(args) passes value as the first argument to the next call. Flow chains associate left to right.
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

## Algebraic and structural operations

Reaper includes a pure, domain-neutral operator library for numeric work,
vectors, matrices, sampled data, and collections. It is not limited to audio.

| Operation | Meaning |
|---|---|
| opposite(value), multiply(a, b), divide(a, b), power(a, b) | Checked scalar arithmetic |
| root(value[, degree]), logarithm(value[, base]), exponential(value[, base]) | Real-domain power and logarithmic transforms |
| replicate(value, count), reverse(values) | Bounded repetition and reversal |
| vector_scale(vector, factor), dot(a, b), distance(a, b) | Vector scaling, dot product, and Euclidean distance |
| differentiate(samples[, step]) | Adjacent forward finite differences |
| integrate(samples[, step]) | Cumulative trapezoidal integration, beginning at zero |
| accumulate(values[, initial]), differences(values) | Prefix sums and adjacent differences |
| quantize(value[, step]) | Round to a positive interval using ties-to-even |
| normalize(values[, mode]) | Min-max scaling or Euclidean unit normalization |
| factorize(integer) | Bounded prime factorization of a positive integer |
| flatten(values), transpose(matrix), matrix_multiply(a, b) | Nested-list and matrix operations |
| unique(values) | Stable scalar deduplication with strict type identity |
| cartesian(a, b), proliferate(choices) | Bounded combinatorial expansion |
| branch(value, functions) | Apply each listed Reaper function to one input |
| transform(values, function) | Map a function over a sequence |

Collection expansion and matrix work are checked against interpreter limits.
Invalid numeric domains, incompatible vector sizes, ragged matrices, and
division by zero raise Reaper runtime diagnostics. These helpers are pure and
do not grant filesystem, network, process, shell, clock, device, or audio-host
access. See [the 20-triad operator matrix](docs/ALGEBRAIC_OPERATOR_MATRIX.md)
for the complete mapping and executable example.

## Execution

~~~sh
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --steps 2000000 examples/flow.rpr
python -m reaper --items 50000 --text-length 500000 examples/flow.rpr
~~~

The default limits are 1,000,000 execution steps, 256 nested function calls, 100,000 collection items and 1,000,000 characters produced by text concatenation. The CLI exposes `--steps`, `--items` and `--text-length`; the Python API exposes the same collection and text limits through `Interpreter` and `run()`.

A quota violation stops execution with a Reaper runtime diagnostic. These limits are resource guardrails, not a security sandbox; do not run untrusted programs under the assumption that the interpreter isolates them from the host process.

Python 3.10+ is required. The interpreter uses only the Python standard library.

## Implementation boundary

Implemented in 0.1: lexer, parser, tree-walk interpreter, lexical closures, lists, functions, flow composition, console I/O, source diagnostics, an execution-step budget, call-depth limits, collection-item limits and text-concatenation limits.

Not implemented yet: static type checking, algebraic effect handlers, semantic-graph storage, native compilation, GPU execution, distributed scheduling, formal verification, package registry, or self-hosting compiler. These are roadmap goals, not current guarantees.
