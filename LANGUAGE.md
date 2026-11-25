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

## System Runtime bridge

Interpreted `.rpr` programs can call the capability-gated System Runtime through the explicit `ffi_open` / `ffi_bind` bridge. The trusted host must attach a provider to the current execution thread before the program starts. Without an attachment or the required capability, the request fails closed.

See [the ABI and bridge contract](docs/SYSTEM_RUNTIME_ABI_V1.md) and [the Reaper example](examples/system_runtime.rpr). This path requires `--allow-native-ffi` and an absolute library path. The scalar AOT backend does not yet lower FFI, and this bridge does not by itself implement DuckOS system calls.
