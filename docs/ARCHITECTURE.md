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

## Optional local backend

The opt-in `reaper-backend` host is an adapter around the Python reference runtime. It is not started by the normal CLI or Studio. The host binds to loopback only, uses bounded asyncio socket I/O and a fixed worker pool, persists idempotency responses in SQLite, and exposes health/readiness, source checking, optional restricted execution and bounded metrics. See [LOCAL_BACKEND.md](LOCAL_BACKEND.md) for the v1 transport contract and exact limitations.

## Integrated product layer

Reaper exposes eighteen in-process product services through `reaper.products` and the Studio product registry. The canonical workflow product name is **Doopraul** (replacing the earlier planning name Patakee). Product services share the Python reference host and do not claim C17 parity. See [INTERNAL_PRODUCTS.md](INTERNAL_PRODUCTS.md) for responsibilities, operations and safety boundaries.
