# Reaper language — quick reference

Reaper 0.2 is an expression-oriented language with a Python reference runtime and a bytecode VM. The native C17 compiler remains a separate, partial implementation.

| Syntax | Meaning |
|---|---|
| `craft name(args) { ... }` | function |
| `make name := value` | immutable binding |
| `vary name := value` | mutable binding |
| `change name = value` | reassignment |
| `yield value` | function result |
| `emit value` | explicit console output |
| `value :: op(args)` | pass value as first argument |
| `[a,b] :: map(fn)` | collection flow |
| `{name: value}` | ordered map literal (computed keys use `[key]: value`) |
| `record.name` / `record?.name` | strict / null-safe map member access |
| `value ?? fallback` | lazy fallback when the left value is `nothing` |
| `keys`, `values`, `entries`, `get`, `put`, `merge`, `pick`, `omit` | map operations |
| `map_values`, `filter_entries`, `group_by`, `count_by` | higher-order map operations |
| `zip`, `enumerate`, `scan`, `take_while`, `drop_while`, `zip_with` | bounded sequence operations |

```reaper
craft double(x) { yield x * 2 }
make total := [1, 2, 3] :: map(double) :: sum()
emit "total = " ++ text(total)
```

Map values are evaluated from left to right. A bare identifier before `:` is a literal text key (`name: value`); use `[key]: value` for a computed key. Member lookup is map-only and never exposes Python object attributes. `?.` returns `nothing` only when its receiver is `nothing`; an absent key still reports an error. `??` evaluates its right side only when the left side is `nothing`. Map helper operations return new maps rather than mutating their inputs.

Rules: explicit effects; no implicit file/network/clock access in ordinary expressions; no silent coercion; bounded steps, call depth and collections. See [runtime limits](docs/RUNTIME_PLATFORM.md).

## Map and sequence example

```reaper
make field := "score"
make user := { name: "Ada", [field]: 9 }
emit user.name
emit user?.nickname ?? "anonymous"
emit user[field]
emit user :: put("level", 3) :: keys() :: join(", ")
```

The same syntax and operators are supported by `treewalk` and `vm` engines in the Python reference implementation. C17 parity is not implied.

## Integrated product layer

Reaper includes eighteen in-process product services, exposed through `reaper --products`, `reaper --product-info Dropaul`, and the Reaper Studio **Внутренние продукты** menu. The workflow product's canonical name is **Dropaul**. Product services use the Python reference runtime; C17 parity is not claimed.
