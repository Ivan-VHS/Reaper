# REAPER / MOST unified architecture

| Principle | Contract |
|---|---|
| One language | REAPER owns syntax, semantics, types and runtime |
| МОСТ | exact Russian aliases to REAPER tokens only |
| Pipeline | source → tokens → AST → checks → canonical IR → backend |
| Mutability | immutable by default; explicit mutation |
| Ownership | deterministic resource lifecycle; no implicit unsafe memory |
| Arithmetic | checked overflow, explicit wrapping/saturating forms |
| Effects | capability-gated host operations |
| Native target | C17, later standards only after conformance |

Python remains the executable compatibility reference until differential tests cover the complete language/CLI. The C17 backend currently emits x86-64 System V ELF assembly for a bounded signed-i64 expression subset only; this is not the DuckOS ABI or a complete native compiler. Native parser/IR milestones do not imply full compiler parity.
