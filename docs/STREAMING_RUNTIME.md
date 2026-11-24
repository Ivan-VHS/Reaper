# Typed results and fused streams

**Status:** implemented in the Python reference runtime.  
**Scope:** bounded single-pass streams, typed result values, strict text/number/time parsing and map aggregation.  
**Native AOT:** stream and result operations are not yet in the native C17 subset; unsupported programs continue to receive an explicit native-compiler diagnostic.

## Design

The runtime exposes two first-class host values:

- `ResultValue<T, E>` represents `Ok(T)` or `Err(E)`. The generic parameters document the contract; the current interpreter does not yet enforce generic types at compile time.
- `StreamValue<T>` wraps an iterable as a bounded, single-use source. Stream `map` and `filter` append operations to a shared pipeline plan. `fold` or `each` consumes the plan in one source loop.

The stream pipeline does not materialize a collection between map/filter stages. Its retained state is the source iterator plus the small list of transformation descriptors. The output of `fold` is the accumulator chosen by the program. Aggregating by service therefore requires memory proportional to the number of distinct services, not the number of log records.

Every source item consumes the interpreter step budget. A stream also enforces `max_collection_items`, including for iterators whose length is not known in advance. A stream can be consumed only once; early termination and failures close an underlying iterator when it exposes `close()`.

This is interpreter-level fusion: the stage chain is executed in one loop without intermediate lists or nested transformation iterators. It is not yet a native IR optimization. The experimental C17 AOT path still supports only its documented scalar subset and must not silently fall back to Python.

## Standard-library API

| API | Contract |
|---|---|
| `ok(value)`, `err(error)` | Construct `ResultValue` values |
| `map_ok(result, fn)` | Transform only an `Ok` payload |
| `map_err(result, fn)` | Transform only an `Err` payload |
| `zip_ok(a, b)`, `zip3_ok(a, b, c)` | Combine successful results; return the first error in argument order |
| `result_is_ok`, `result_is_err` | Inspect the result variant |
| `result_value`, `result_error` | Read the corresponding payload; reading the wrong variant raises a runtime error |
| `stream(iterable)` | Create a bounded, single-use stream |
| `map(stream, fn)`, `filter(stream, fn)`, `keep(stream, fn)` | Append lazy fused stages; list inputs retain eager backwards-compatible behavior |
| `fold(stream, initial, fn)` | Consume a stream once and produce an accumulator |
| `split_limit(text, separator, max_splits)` | Split at most `max_splits` times; the unsplit tail is preserved |
| `map_new()` | Create an empty map |
| `map_alter(map, key, fn)` | Call `fn(present, current)`, then atomically assign its result to the key |
| `map_values(map, fn)` | Transform map values into a new map |
| `to_int`, `to_float` | Strict conversions; booleans and non-finite numbers are rejected |
| `try_int`, `try_float` | Non-throwing conversions that return `ResultValue` |
| `is_finite(number)` | Check numeric finiteness; non-numeric inputs return false |
| `parse_rfc3339(text)`, `try_rfc3339(text)` | Parse an ISO/RFC 3339 timestamp with an explicit timezone |
| `analysis_empty()` | Create the standard empty log-analysis map |

`map_alter` evaluates its callback before assigning the new value. If the callback fails, the map is unchanged. It updates the provided map in place to keep per-record aggregation close to constant-time; this mutation is explicit at the call site.

The language currently has no associated-function syntax or record type declarations, so the Reaper source-level equivalent of `Analysis.empty()` is `analysis_empty()`. The returned map uses string keys and can be inspected with normal map indexing.

The timestamp parser returns Python's timezone-aware `datetime` representation. It rejects timezone-free timestamps, invalid dates and times, leap seconds that the host datetime representation cannot express, and fractional seconds with more than six digits rather than silently truncating precision.

## Example

```reaper
craft double(value) {
    yield value * 2
}

craft above_three(value) {
    yield value > 3
}

craft add(accumulator, value) {
    yield accumulator + value
}

make total := [1, 2, 3, 4]
    :: stream()
    :: map(double)
    :: filter(above_three)
    :: fold(0, add)

emit total
```

The result is `18`. The map and filter stages are lazy and the fold consumes the original source exactly once.

For recoverable parsing, `try_int`, `try_float` and `try_rfc3339` return results. `zip3_ok` preserves the first encountered error; `map_ok` and `map_err` transform only the matching variant.

## Log-analysis building blocks

A one-pass log analyzer can use this pattern:

1. `split_limit(line, " | ", 4)` preserves delimiters inside the message tail.
2. `try_rfc3339`, `try_int` and `try_float` build typed parse results without exceptions for malformed values.
3. `zip3_ok` combines independent field parses.
4. `fold(stream(lines), analysis_empty(), update)` counts valid and malformed records and updates service summaries as each record arrives.
5. `map_alter` updates a service summary without retaining every source record.

The log parser must still enforce domain-specific constraints such as HTTP status range 100–599, server errors 500–599, non-empty service names and non-negative latency. Those are application validation rules, not implicit behavior of general-purpose numeric conversion.

## Validation

Run the focused suite:

```sh
python -m unittest discover -s tests -p test_streaming_runtime.py -v
```

Run the complete Python suite:

```sh
python -m unittest discover -s tests -v
```

When changing the stream implementation, retain tests for single-use behavior, lazy stage composition, per-stream quotas, error propagation, tail-preserving splitting and callback atomicity. Do not claim a speedup over a loop or another language without reproducible benchmarks on the same workload.
