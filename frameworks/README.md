# Reaper Framework Family

This directory contains the first Reaper-source implementation slice for ten independent frameworks.

| Framework | Primary source | Initial responsibility |
|---|---|---|
| Lokaliza | `Lokaliza/src/locale.rpr` | Locale registry, fallback and catalog lookup |
| Sealise | `Sealise/src/blueprint.rpr` | Project blueprints and structural coverage |
| Blebby | `Blebby/src/package.rpr` | Package metadata, versions and dependency checks |
| Centen | `Centen/src/resource.rpr` | Bounded resource accounting |
| Kaso | `Kaso/src/template.rpr` | Template slots and deterministic rendering |
| Shinnn | `Shinnn/src/graph.rpr` | Architecture graph validation |
| Porteo | `Porteo/src/lifecycle.rpr` | Component lifecycle and dependency readiness |
| Portable Bortable | `Portable-Bortable/src/target.rpr` | Target profiles and compatibility |
| SWO | `SWO/src/pipeline.rpr` | Workflow states and stage dependencies |
| ScoHOPE | `ScoHOPE/src/application.rpr` | Application profiles and lifecycle |

## Source budget

Each framework has an implementation-source target of exactly **666,666 Unicode characters**. The machine-readable manifest records the initial source count and remaining balance. Only implementation files under each framework's `src/` directory count toward the target. Documentation, tests, generated files and manifests do not count.

Source counts include whitespace and comments in tracked `.rpr` files. Source files use UTF-8 and LF line endings. The count is recalculated from the committed source files; it is not inferred from line count or repository size.

## Compatibility boundary

The first slice uses the current `.rpr` surface: `craft`, `make`, `vary`, `change`, `yield`, `when/otherwise`, `loop while`, lists, indexing, imports and exports. It is source code in Reaper, but it is **not yet native-AOT complete**: the repository's documented native backend does not currently compile list operations, module imports or the full collection runtime.

The framework contracts are kept narrow and explicit. Shared lifecycle and runtime services remain owned by ДОМ; these modules do not introduce a competing runtime. No filesystem, process, network, shell, clock or hardware authority is added by these pure transformations.

## Status

This is a bootstrap implementation slice, not a completed product release. Each subsystem still needs focused positive/negative tests, resource-limit checks, source-span diagnostics, module-graph validation and integration evidence before its status can be raised.
