# Reaper project maturity

**Current stage:** 04 — Ascension  
**Assessment:** provisional  
**Next stage:** 05 — Vanguard  
**Canonical ladder:** [DAK Engineering Maturity Ladder](https://github.com/Ivan-VHS/DAK/blob/main/docs/PROJECT_EVOLUTION_LADDER.md)  
**Machine record:** [`.github/project-ladder.v1.json`](../.github/project-ladder.v1.json)

The recorded stage is the highest cumulative gate currently supported by repository evidence. It is not a release-quality score and does not imply that later-stage capabilities exist.

## Next gate — Vanguard

- Compile and execute a declared .rpr subset through the native compiler/runtime on its declared targets.
- Add reference/native parity fixtures and versioned ABI compatibility tests.
- Record reproducible target builds and measured CPU, memory and resource budgets.

## Assessment limits

This record is provisional because the full target build, test matrix and relevant integration workflow were not re-run during ladder adoption. Existing documentation and CI definitions are evidence references, not a new certification.

## Promotion procedure

Update this record in the same pull request as implementation. A stage may be marked `met` only when every required evidence category is linked to an existing repository artifact. `verified` additionally requires a pinned commit, workflow, environment, CI run URL, passing test evidence and passing CI evidence. Higher stages remain pending until all lower cumulative gates remain satisfied.
