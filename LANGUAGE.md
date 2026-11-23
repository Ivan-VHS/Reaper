# Reaper language — quick reference

Reaper 0.2 is an expression-oriented language with a Python reference runtime, bytecode VM, developer tooling, and an experimental scalar AOT route through C17.

| Syntax | Meaning |
|---|---|
| `craft name(args) { ... }` | function |
| `make name := value` | immutable binding |
| `vary name := value` | mutable binding |
| `change name := value` | reassignment |
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

## Integrated product layer

Reaper includes eighteen in-process product services, exposed through `reaper --products`, `reaper --product-info Dropaul`, and the Reaper Studio **Внутренние продукты** menu. The workflow product's canonical name is **Dropaul**. Product services use the Python reference runtime; C17 parity is not claimed.

## Native AOT subset

The experimental AOT compiler accepts scalar bindings, top-level integer functions, `yield`, `emit`, `when`/`otherwise`, `loop while`, checked i64 arithmetic, comparisons, booleans, and simple strings. It emits portable C17 and uses an installed GCC/Clang-compatible toolchain to build a host executable:

```sh
python -m reaper program.rpr --emit-c program.c
python -m reaper program.rpr --native program
```

Lists, `each`, collection pipelines, closures, modules, decimals, `nothing`, dynamic dispatch, async/effects, and arbitrary FFI are deliberately outside this first native slice. The Python runtime remains authoritative for those constructs. See [Native AOT Compiler](docs/NATIVE_COMPILER.md).
