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
| `attempt { ... } recover error { ... } finally { ... }` | recover language runtime errors and always run cleanup |
| `throw value` | raise a catchable language runtime error with the displayed value |
| `recover` or `finally` | either clause may be used alone; at least one is required |
| `value :: op(args)` | pass value as first argument |
| `[a,b] :: map(fn)` | collection flow |

```reaper
craft double(x) { yield x * 2 }
make total := [1, 2, 3] :: map(double) :: sum()
emit "total = " ++ text(total)
```

Russian exact aliases: `попытка` → `attempt`, `обработать` → `recover`, `наконец` → `finally`, `бросить` → `throw`.

`recover` receives the runtime diagnostic as text. `finally` runs on success, recovery, uncaught language errors and early function return. The execution-budget error is deliberately not recoverable; `finally` code remains subject to the same step budget. This is implemented in the Python reference runtime and VM; native C17 parity is not claimed.

Rules: explicit effects; no implicit file/network/clock access in ordinary expressions; no silent coercion; bounded steps, call depth and collections. See [runtime limits](docs/RUNTIME_PLATFORM.md) and [structured error handling](docs/STRUCTURED_ERROR_HANDLING.md).

## Integrated product layer

Reaper includes eighteen in-process product services, exposed through `reaper --products`, `reaper --product-info Dropaul`, and the Reaper Studio **Внутренние продукты** menu. The workflow product's canonical name is **Dropaul**. Product services use the Python reference runtime; C17 parity is not claimed.
