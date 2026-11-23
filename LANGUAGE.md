# Reaper systems language — quick reference

Reaper is moving toward a low-level systems and hardware language for firmware, embedded software and platform development. The current product keeps its expression-oriented .rpr language and Python compatibility runtime while the native compiler and hardware contracts are expanded. See [the systems-language architecture](docs/HARDWARE_LANGUAGE.md) for the migration plan and implemented boundaries.

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

Rules: explicit effects; no implicit file/network/clock access in ordinary expressions; no silent coercion; bounded steps, call depth and collections. See [runtime limits](docs/RUNTIME_PLATFORM.md).\n\n## Static type analysis\n\nThe optional `reaper typecheck program.rpr` command runs conservative type inference over the existing AST. It checks supported numeric and text operators, collection indexes and iteration, mutable bindings, and known call arity. Unknown values at module and host boundaries remain `Any`. This is a first semantic-analysis slice, not yet a complete sound type system with source annotations, user generics, null-flow refinement or exhaustive pattern matching. See [Polyglot capability layer](docs/POLYGLOT_CAPABILITY_LAYER.md) for the capability map and implementation status.

## Integrated product layer

Reaper includes eighteen in-process product services, exposed through `reaper --products`, `reaper --product-info Dropaul`, and the Reaper Studio **Внутренние продукты** menu. The workflow product's canonical name is **Dropaul**. Product services use the Python reference runtime; C17 parity is not claimed.

## Native AOT subset

The experimental AOT compiler accepts scalar bindings, top-level integer functions, `yield`, `emit`, `when`/`otherwise`, `loop while`, checked i64 arithmetic, comparisons, booleans, and simple strings. It emits portable C17 and uses an installed GCC/Clang-compatible toolchain to build a host executable:

```sh
python -m reaper program.rpr --emit-c program.c
python -m reaper program.rpr --native program
```

Lists, `each`, collection pipelines, closures, modules, decimals, `nothing`, dynamic dispatch, async/effects, and arbitrary FFI are deliberately outside this first native slice. The Python runtime remains authoritative for those constructs. The C17 MMIO adapter validates descriptors and capability grants through a host-supplied bus; it does not map physical memory. QCS remains a separate validation frontend. See [Native AOT Compiler](docs/NATIVE_COMPILER.md) and [Hardware Language](docs/HARDWARE_LANGUAGE.md).


## Map access and conversion helpers

| Builtin | Contract |
|---|---|
| `has_key(map, key)` | true when a map contains the text key; rejects non-maps and non-text keys |
| `get(map, key[, default])` | reads a text-keyed map entry or returns the explicit default (otherwise `nothing`) |
| `to_int(value)` | converts an integer, an integral finite number, or decimal integer text; rejects booleans and fractional values |
| `to_int(value, fallback)` | returns the converted integer, or converts the explicit fallback when conversion fails |
| `to_str(value)` | formats a Reaper value as text |
| `len(value)` | bounded length of text, lists, maps and ranges; `size(value)` remains available |

The reference runtime accepts maps supplied by JSON input or host adapters. The current source grammar does not yet include map literals, property access (`.field`) or arrow-function expressions. Use bracket indexing for known keys and `has_key`/`get` for optional fields.

## Duck pipeline example

`examples/duck_pipeline.rpr` demonstrates pure name normalization, map-based duck inspection, range validation, tagged success/error values, and `map`/`filter` composition. It reads its records from `examples/data/duck_pipeline_input.json`.

Run and validate it with:

```sh
python -m reaper --check examples/duck_pipeline.rpr
python -m reaper examples/duck_pipeline.rpr
python -m unittest tests.test_duck_pipeline -v
```

The example uses `[true, value]` and `[false, [code, message, details]]` as an explicit Result convention. It is a Python reference-runtime example; collection pipelines and dynamic map input are not part of the current native C17 AOT subset.
