# Reaper language — quick reference

Reaper 0.1 is an expression-oriented Python-hosted interpreter. It is not yet a complete native compiler.

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

```reaper
craft double(x) { yield x * 2 }
make total := [1, 2, 3] :: map(double) :: sum()
emit "total = " ++ text(total)
```

Flow built-ins include `all`, `any`, `none`, `count`, `find`, `find_index`, `take_while`, `drop_while`, `enumerate`, `zip`, `scan` and `window`. Predicates and reducers are ordinary Reaper functions; every traversed item is charged to the execution budget. See [the Flow Toolkit contract](docs/FLOW_TOOLKIT.md).\n\nRules: explicit effects; no implicit file/network/clock access in ordinary expressions; no silent coercion; bounded steps, call depth and collections. See [runtime limits](docs/RUNTIME_PLATFORM.md).

## Integrated product layer

Reaper includes eighteen in-process product services, exposed through `reaper --products`, `reaper --product-info Dropaul`, and the Reaper Studio **Внутренние продукты** menu. The workflow product's canonical name is **Dropaul**. Product services use the Python reference runtime; C17 parity is not claimed.
