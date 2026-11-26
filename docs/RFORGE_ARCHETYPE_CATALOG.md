# RForge proposed product archetypes

**Contract:** `reaper.rforge.archetype-catalog.v1`  
**Status:** proposed names and ordered profile tokens; semantic contracts and implementations are pending

This catalogue records twenty product directions in ten mirrored pairs. Each product has an independent identity. Within each pair, the second product reverses the two profile tokens of the first.

## Pair catalogue

| Pair | Forward product | Forward profile | Reverse product | Reverse profile |
|---|---|---|---|---|
| 01 | Plague | Soft Frame | Outbreak | Frame Soft |
| 02 | Pestilence | Frame Saas | Malady | Saas Frame |
| 03 | Epidemic | Framework native | Miasma | native Framework |
| 04 | Pandemic | Program Summary | Fever | Summary Program |
| 05 | Scourge | System Control | Bane | Control System |
| 06 | Blight | Tunnel Justice | Curse | Justice Tunnel |
| 07 | Calamity | native Realisation | Menace | Realisation native |
| 08 | Affliction | UI Unreal | Cataclysm | Unreal UI |
| 09 | Infestation | Concrete Cosmos | Devastation | Cosmos Concrete |
| 10 | Contagion | base Space | Desolation | Space base |

## Composition rules

- Product names are independent identities; they are not aliases for the RForge platform.
- The two profile tokens are ordered inputs. RForge must preserve their order exactly.
- A reversed pair is a distinct composition candidate, not an automatic alias or duplicate.
- RForge may compare both candidates, but it must not assume that reversing tokens has no semantic effect.
- The profile tokens are user-supplied vocabulary. Their exact runtime meaning, product-family assignment, interfaces, permissions and acceptance criteria must be supplied by a semantic contract before code generation.
- Product kind remains `pending` until the architecture is classified as a framework, multitool, multiapp, framework bundle, multiframe, multiwork or frame/application/tool suite.
- All twenty entries remain `proposal`; no source generation, compilation, installation or executable capability is claimed.

## Why this is useful

The mirrored pairs give RForge a deterministic way to explore composition order. Once the token meanings have contracts, the planner can construct both orderings, compare dependency graphs and report whether the order changes lifecycle ownership, capability routing, UI composition, deployment shape or other measurable properties.

The machine-readable catalogue is `examples/rforge/product-archetypes.v1.json`.
