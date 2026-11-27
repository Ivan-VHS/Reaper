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

## Expressive syntax contract

Reaper favors concise composition without hidden semantics. The current `::` first-argument flow form remains the canonical pipeline operator; reusable patterns belong in named `craft` functions and standard-library combinators. Localized keyword aliases are explicit exact mappings, not fuzzy spelling rules. Every new syntax form must be specified and tested across the canonical frontend, runtime/VM, diagnostics and editor services before it is described as available. See [Expressive Precision: Syntax Design Rules v1](docs/EXPRESSIVE_PRECISION_SYNTAX_V1.md).

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
