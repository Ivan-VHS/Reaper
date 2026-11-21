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

Rules: explicit effects; no implicit file/network/clock access in ordinary expressions; no silent coercion; bounded steps, call depth and collections. See [runtime limits](docs/RUNTIME_PLATFORM.md).
