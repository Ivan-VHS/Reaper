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

Python 0.2 is the executable reference for the documented language slice. The tree-walk and verified stack VM have conformance coverage for that slice; full C17 language parity remains a separate milestone. Native parser/IR milestones do not imply a completed native compiler.
