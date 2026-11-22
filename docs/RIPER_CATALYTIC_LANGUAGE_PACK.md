# RIPER Catalytic Language Pack

This pack extends the Python reference runtime with bounded functional,
data, result/option, snapshot, numeric and text constructions. It does not
claim full C17-native parity.

## New operators

| Form | Meaning |
|---|---|
| value |> transform(args) | Flow operator; equivalent to value :: transform(args) |
| value ?? fallback | Null coalescing; evaluates fallback only when value is nothing |
| value in sequence | Membership test for text, lists, tuples, ranges and map keys |

## Result and option forms

ok(value), err(message), is_ok(result), is_err(result), unwrap(result),
unwrap_or(result, fallback), result_map(result, fn), result_bind(result, fn),
try_call(fn, args...), recover(result, fallback), some(value), is_some(value),
is_none(value), some_value(value) and coalesce(value, fallback).

try_call returns a tagged result. It catches language/runtime argument failures;
it does not suppress process termination, keyboard interrupts or arbitrary base
exceptions.

## State and transformation forms

snapshot(value) and clone(value) make a bounded deep copy of scalar, list and
map data. reflash(value, fn...) applies functions from left to right.
rebind(map, updates) returns a new map with updates applied without mutating input.\nmap_of(key, value, ...) and map_from_entries(pairs) construct maps for programs.

## Collection forms

zip, enumerate, all_of, any_of, find, find_index, count_by, take_while,
drop_while, scan, group_by, partition_by, window, transpose, interleave,
compact, pluck, keys, values, entries, merge, get_or, has_key, put, remove_key,
slice and flat_map.

All collection-producing operations enforce the interpreter item limit.
group_by requires hashable callback results; transpose requires equal row lengths.

## Numeric and text forms

Numeric: clamp, lerp, sign, is_even, is_odd, gcd, lcm, mean, median, variance,
stdev, sum_by, min_by and max_by.

Text: words, lines, char_at, pad_left, pad_right, repeat_text, count_text,
slice_text.

## Example

~~~reaper
craft double(x) { yield x * 2 }
craft positive(x) { yield x > 0 }

make data := [-2, 1, 3, 5]
make transformed := data
    |> keep(positive)
    |> reflash(double, double)

emit transformed
emit some_value(some("RIPER"))
emit 0 ?? 99
emit 7 in [2, 5, 7]
~~~

## Evolution policy

The huge iteration/function counts in the design request are treated as
capacity goals, not fabricated completion numbers. New constructions must have
a parser/runtime contract, limits, tests, completion support and truthful
maturity metadata before being called implemented. Reserved catalogue entries
remain distinct from executable behavior.
