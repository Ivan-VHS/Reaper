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

Python 0.1 remains the reference until differential tests cover the complete language/CLI. Native parser/IR milestones do not imply a completed compiler.


## Hardware contract

The C17 native core now contains a checked MMIO descriptor and bus-adapter contract. It is intentionally not described as physical-memory access: only a trusted host adapter can perform device transactions. The long-term source-language and backend design is specified in [HARDWARE_LANGUAGE.md](HARDWARE_LANGUAGE.md).

## Source provenance contract

Python reference path: source → position-aware lexer tokens → AST nodes → semantic/static checks → canonical stack IR → tree-walk or VM execution. Tokens carry a `Span` with source name, half-open UTF-8 byte offsets, and 1-based start/end line-column coordinates. Lowering retains the introducing token on each IR instruction; `CanonicalIR.source_map` exposes a deterministic instruction-index map.

Native C17 path: source → position-aware C lexer → bounded expression AST → checked integer IR → supported native operations. Token, AST and IR structures retain half-open UTF-8 byte offsets; line and column remain 1-based code-point coordinates. The native parser/lowerer is still a deliberately limited expression slice, not a drop-in native implementation of the complete Python grammar or stack IR.

МОСТ aliases are exact lexical spellings normalized to canonical Reaper keywords. Reserved aliases and catalogued operators do not acquire executable semantics merely by being recognized. Semantic equivalence is required wherever two profiles do parse the same feature; unsupported features must fail with a diagnostic rather than silently diverge.

Across the ecosystem, Reaper is integrated through narrow, reviewable boundaries: process-based source checking in DuckOS, opt-in integer-expression ABI use in OPlague and VentuSample, and CI policy validation in Pytyliki. Each specialist application retains ownership of its domain-specific runtime and side effects. See [Reaper repository adoption standard](REAPER_REPOSITORY_ADOPTION_STANDARD.md).
