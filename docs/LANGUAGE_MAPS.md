# Reaper 0.2 — map and sequence language extension

This extension adds first-class ordered map literals to the Python reference
language and the canonical bytecode VM.

## Syntax

- `{name: value, "other": value}` constructs an ordered map. A bare identifier
  before the colon is a literal text key. Use `[key]: value` for a computed key.
- `record.name` reads a map member and reports an error when the key is absent.
- `record?.name` returns `nothing` when the receiver is `nothing`; it does not
  hide missing-key errors and does not access host-language object attributes.
- `value ?? fallback` evaluates `fallback` only when `value` is `nothing`.

Map entries are evaluated from left to right. Repeated keys use the last value.
Map construction, map helpers and sequence helpers respect the configured
collection limit. Map transformations return new maps; source maps are not
mutated.

## Built-ins

Map inspection and transformation:

`keys`, `values`, `entries`, `has_key`, `get`, `put`, `merge`,
`pick`, `omit`, `from_entries`, `map_values`, `filter_entries`.

Sequence operations:

`zip`, `enumerate`, `any`, `all`, `compact`, `group_by`, `count_by`,
`scan`, `take_while`, `drop_while`, `zip_with`.

Higher-order map callbacks receive `(key, value)`; sequence callbacks receive
the item (or accumulator/item pair for `scan` and two zipped items for
`zip_with`). Callback iterations are charged to the interpreter's execution
step budget.

## Engine parity

The syntax lowers through canonical IR into the VM. The conformance suite runs
the same examples under `treewalk` and `vm`. This does not claim equivalent
support in the separate native C17 compiler track.
