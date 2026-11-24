# Architecture

| Layer | Responsibility |
|---|---|
| CLI / Studio | source input, run/check/debug, reports |
| Lexer | deterministic tokens and source spans |
| Python parser/runtime | reference semantics, scopes, values, quotas |
| Semantic IR | versioned typed expression graph, source provenance, contracts and diagnostics |
| Execution IR | verified stack instructions consumed by the VM; kept separate from semantic IR |
| Native C17 | token stream, expression AST, checked scalar IR, limited lowering |
| MOST | exact keyword canonicalization before the same parser |
| QCS | independent hardware-domain syntax validation |
| Adapters | versioned JSON and explicitly selected native ABI |
| Tests | syntax, semantics, bounds, negative cases and integrations |

Reaper source → UTF-8 source spans → tokens → AST → semantic IR → analysis/contracts → execution IR → bounded reference runtime. The semantic graph is versioned and source-aware; the existing stack `CanonicalIR` remains the VM execution format. The C17 track is separate until full language conformance. Studio is Windows-only.

## Integrated product layer

Reaper exposes eighteen in-process product services through `reaper.products` and the Studio product registry. The canonical workflow product name is **Doopraul** (replacing the earlier planning name Patakee). Product services share the Python reference host and do not claim C17 parity. See [INTERNAL_PRODUCTS.md](INTERNAL_PRODUCTS.md) for responsibilities, operations and safety boundaries.
