# Reaper language — quick reference

Reaper 0.2 is an expression-oriented language with a Python reference runtime and a verified stack-VM execution path. The C17 implementation remains a partial native track, not a complete compiler.

| Syntax | Meaning |
|---|---|
| `let name = value` / `const name = value` | immutable binding |
| `mut name = value` | mutable binding |
| `name = value` | assignment to existing mutable binding |
| `fn name(args) { ... }` | function |
| `return value` | function result |
| `if condition { ... } else { ... }` | conditional |
| `for item in collection { ... }` | collection loop |
| `while condition { ... }` | condition loop |
| `break` / `continue` | nearest-loop control |
| `{ "key": value }` / `value.field` | map literal and field lookup |
| `a in collection` | membership |
| `a ?? fallback` | null-only lazy fallback |
| `value :: op(args)` | pass value as first argument |

Legacy forms remain accepted: `make`, `vary`, `change`, `craft`, `yield`, `when`, `otherwise`, `each`, and `loop while`.

```reaper
fn double(x) { return x * 2 }
let config = {"name": "Reaper"}
mut total = 0
for item in [1, 2, 3] {
    if item == 2 { continue }
    total = total + double(item)
}
emit config.name
emit total
```

The tree-walk and VM engines share the 0.2 conformance tests. Reaper remains dynamically typed; struct/enum declarations, generics, static typing, async/await and complete C17 parity are not implemented. Ordinary expressions have no implicit filesystem or network effects. Runtime steps, call depth, collections, text, heap and open resources are bounded.

See [Language Reference 0.2](docs/LANGUAGE_REFERENCE_0.2.md) and [runtime limits](docs/RUNTIME_PLATFORM.md).
