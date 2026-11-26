# RForge Reaper framework archetypes

**Contract:** `reaper.rforge.archetype-catalog.v1`  
**Status:** twenty Reaper source modules are present; runtime validation is pending

The original ten mirror pairs are now implemented as twenty distinct Reaper `.rpr` framework modules. The pair relation is still an ordered token reversal, and each side has a distinct API and responsibility.

See [the full framework collection](../frameworks/rforge/README.md) for descriptions, public APIs, invariants, imports and current runtime/native-AOT limits.

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

- Product names remain independent identities.
- Profile tokens remain ordered and are preserved exactly as supplied.
- Reverse members are distinct framework candidates, not aliases.
- All twenty entries are classified as `framework` and point to an importable Reaper source module.
- Source presence is not the same as runtime verification or native compilation.
- No executable capability is claimed until the framework passes runtime and contract tests.

The machine-readable implementation catalogue is [`examples/rforge/frameworks.v1.json`](../examples/rforge/frameworks.v1.json).
