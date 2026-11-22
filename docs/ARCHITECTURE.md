# Architecture

| Layer | Responsibility |
|---|---|
| CLI / Studio | source input, run/check/debug, reports |
| Lexer | deterministic tokens and source spans |
| Python parser/runtime | reference semantics, scopes, values, quotas |
| Native C17 | complete-program Pratt/statement AST, HIR name/scope/mutability and basic type checks, checked i64 IR/lowering, System V and DuckOS DABI64 expression assembly targets |
| MOST | exact keyword canonicalization before the same parser |
| QCS | independent hardware-domain syntax validation |
| Adapters | versioned JSON and explicitly selected native ABI |
| Tests | syntax, semantics, bounds, negative cases and integrations |

Reaper source → tokens → AST → bounded Python reference runtime → explicit output. The C17 path now parses full program structure and performs HIR name/scope/mutability/basic-type checks, while native machine-code lowering remains limited to checked i64 expressions. Two explicit assembly targets exist: x86-64 System V and the separate DuckOS DABI64 v1 ABI. MIR/CFG, general LIR, whole-program codegen, object writing/linking and the DuckOS loader/kernel/runtime are still pending. Studio is Windows-only.

## Integrated product layer

Reaper exposes eighteen in-process product services through `reaper.products` and the Studio product registry. The canonical workflow product name is **Doopraul** (replacing the earlier planning name Patakee). Product services share the Python reference host and do not claim C17 parity. See [INTERNAL_PRODUCTS.md](INTERNAL_PRODUCTS.md) for responsibilities, operations and safety boundaries.
