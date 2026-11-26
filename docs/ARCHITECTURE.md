# Architecture

| Layer | Responsibility |
|---|---|
| CLI / Studio | source input, run/check/debug, reports |
| Lexer | deterministic tokens and source spans |
| Python parser/runtime | reference semantics, scopes, values, quotas |
| Native C17 | token stream, expression AST, checked IR, limited lowering |
| MOST | exact keyword canonicalization before the same parser |
| QCS | independent hardware-domain syntax validation |
| Adapters | versioned JSON and explicitly selected native ABI |
| Tests | syntax, semantics, bounds, negative cases and integrations |

Reaper source → tokens → AST → bounded reference runtime → explicit output. The C17 track is separate until full language conformance. Studio is Windows-only.

## AESTHETICA evaluation layer

`frameworks/aesthetica/core.rpr` is an independently importable reference-runtime module. It validates caller-supplied evidence, context weights and ordered stage contracts; aggregates beauty and ugliness as independent axes; and emits versioned reports, source-provenance findings and same-object profile comparisons. `examples/aesthetica.rpr` is its executable acceptance example. The module uses only the current Reaper grammar and built-ins. It performs no I/O and does not mutate evaluated objects. Typed records, compiler-generated Span integration, native C17 parity and Studio/LSP presentation remain future gates; see [AESTHETICA](AESTHETICA.md).

## AESTHETICA evaluation layer

`frameworks/aesthetica/core.rpr` is an independently importable reference-runtime module. It validates caller-supplied evidence, context weights and ordered stage contracts; aggregates beauty and ugliness as independent axes; and emits versioned reports, source-provenance findings and same-object profile comparisons. `examples/aesthetica.rpr` is its executable acceptance example. The module uses only the current Reaper grammar and built-ins. It performs no I/O and does not mutate evaluated objects. Typed records, compiler-generated Span integration, native C17 parity and Studio/LSP presentation remain future gates; see [AESTHETICA](AESTHETICA.md).

## Integrated product layer

Reaper exposes eighteen in-process product services through `reaper.products` and the Studio product registry. The canonical workflow product name is **Doopraul** (replacing the earlier planning name Patakee). Product services share the Python reference host and do not claim C17 parity. See [INTERNAL_PRODUCTS.md](INTERNAL_PRODUCTS.md) for responsibilities, operations and safety boundaries.
