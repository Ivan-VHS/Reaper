# REAPER / MOST — 813 feature proposal IDs

The registry contains proposals and acceptance areas; it does not claim 813 implemented capabilities.

| IDs | Domain | Owner |
|---|---|---|
| 1–147 | original feature specifications | language/spec |
| 148–220 | REAPER extensions and exact MOST aliases | lexer/parser |
| 221–310 | types, contracts, mathematics | type system |
| 311–410 | streams, concurrency, memory | runtime |
| 411–510 | data, schemas, text, rules | standard library |
| 511–610 | safety, effects, capability policy | checker/runtime |
| 611–710 | tooling, tests, debugging, profiling | toolchain |
| 711–813 | host and system integration | adapters |

Stable IDs are never reused. Status: proposed → specified → implemented → tested, or deprecated. An implemented status requires source plus positive/negative acceptance tests.

The API contract registry and symbolic-token lexeme catalogue are separate versioned artefacts; they must not be conflated.
