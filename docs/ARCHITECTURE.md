# Architecture

| Layer | Responsibility |
|---|---|
| CLI / Studio | source input, run/check/debug, reports |
| Reaper self-hosting frontend | Reaper-written tokenization, expression parsing, semantic checks and expression IR/bytecode lowering | partial bootstrap; reference-hosted |
| Lexer | deterministic tokens and source spans |
| Python parser/runtime | reference semantics, scopes, values, quotas |
| Native C17 | token stream, expression AST, checked IR, limited lowering |
| MOST | exact keyword canonicalization before the same parser |
| QCS | independent hardware-domain syntax validation |
| Adapters | versioned JSON and explicitly selected native ABI |
| Native architecture registry | 66 stable concepts, nine layers, bounded dependency-graph validation and deterministic ordering |
| Tests | syntax, semantics, bounds, negative cases and integrations |

Reaper source → tokens → AST → bounded reference runtime → explicit output. The C17 track is separate until full language conformance. Studio is Windows-only.

## Integrated product layer

Reaper exposes eighteen in-process product services through `reaper.products` and the Studio product registry. The canonical workflow product name is **Doopraul** (replacing the earlier planning name Patakee). Product services share the Python reference host and do not claim C17 parity. See [INTERNAL_PRODUCTS.md](INTERNAL_PRODUCTS.md) for responsibilities, operations and safety boundaries.


## Architecture foundation registry

The native C17 core exposes a stable 66-concept architecture catalog and nine semantic layers through include/reaper/architecture.h. It provides exact key/Russian-name lookup, bounded dependency graph validation, cycle detection and deterministic dependency-first ordering. The registry is metadata and graph validation only: it does not instantiate runtimes, containers, host services or hardware access. See [REAPER_ARCHITECTURE_FOUNDATION_66.md](REAPER_ARCHITECTURE_FOUNDATION_66.md).
