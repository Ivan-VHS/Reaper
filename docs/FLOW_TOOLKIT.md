# Flow Toolkit

The Python reference runtime exposes bounded collection combinators through the same built-in registry used by both the tree-walk and VM engines.

## Predicate operations

| Function | Contract |
|---|---|
| `all(values, predicate)` | true when every item satisfies the predicate; true for an empty sequence |
| `any(values, predicate)` | true when at least one item satisfies the predicate; stops on the first match |
| `none(values, predicate)` | true when no item satisfies the predicate |
| `count(values, predicate)` | number of items satisfying the predicate |
| `find(values, predicate)` | first matching item, or `nothing` |
| `find_index(values, predicate)` | index of the first match, or `nothing` |

Predicates are Reaper functions and receive one item. Predicate operations validate the callback and charge each inspected item to the interpreter's execution-step budget.

## Sequence operations

| Function | Contract |
|---|---|
| `take_while(values, predicate)` | prefix before the first item that fails the predicate |
| `drop_while(values, predicate)` | suffix beginning at the first item that fails the predicate |
| `enumerate(values, start := 0)` | list of `[index, value]` pairs |
| `zip(left, right)` | list of pairs, stopping at the shorter input |
| `scan(values, initial, function)` | running fold results, excluding the initial accumulator |
| `window(values, width, step := 1)` | overlapping or stepped full-width windows; incomplete tails are omitted |

All input sequences use the existing bounded sequence contract: lists, tuples, text and ranges. Widths, steps and enumeration offsets must be whole numbers; window width and step must be positive. Results are capped by the configured collection-item limit. Text slicing preserves text for `take_while` and `drop_while`; `window` returns a list of text windows when its input is text.

## Examples

```reaper
craft positive(value) { yield value > 0 }
craft add(left, right) { yield left + right }

make values := [1, 2, 3, 0, 4]
emit values :: all(positive)
emit values :: take_while(positive)
emit enumerate(values, 1)
emit [1, 2, 3] :: scan(0, add)
emit window([1, 2, 3, 4], 2, 1)
```

The implementation is shared by the reference runtime's tree-walk and VM call paths. It does not claim native C17 parity. Verify both engines with:

```sh
python -m unittest discover -s tests -p 'test_flow_toolkit.py' -v
```
