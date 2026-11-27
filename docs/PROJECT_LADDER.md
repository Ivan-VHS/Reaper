# Project Evolution Ladder — Reaper

**Current rung:** 04 — **Ascension**  
**Assessment:** Provisional documentation review · 25 November 2026  
**Next rung:** 05 — **Vanguard**

This is a project-level maturity snapshot under the [canonical Ivan-VHS Project Evolution Ladder](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PROJECT_EVOLUTION_LADDER.md). It does not replace capability statuses, release versioning or domain-specific stage names. SemVer remains unchanged.

## Evidence considered

- [`docs/IMPLEMENTATION_ROADMAP.md`](https://github.com/Ivan-VHS/Reaper/blob/main/docs/IMPLEMENTATION_ROADMAP.md) — Reference runtime, Studio, LSP/DAP and partial native C17 work are tracked as connected workstreams with explicit limits.
- [`docs/FEATURES.md`](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEATURES.md) — The feature matrix separates available reference-runtime behavior from partial native compiler and MMIO contracts.

The initial rung is **provisional**: it was assigned from documented implementation boundaries. No source-level deep audit, test run or CI rerun was performed as part of ladder adoption. It is not a new certification and must not upgrade individual capability statuses.

## Known limits

- Native C17 is not feature-equivalent to the reference runtime and is not a general machine-code backend.
- No test or CI workflow was re-run during ladder adoption.

## Next promotion gate — 05 Vanguard

- Compile and execute a declared .rpr subset through the native path.
- Add reference/native parity fixtures and host ABI validation for that subset.
- Run reproducible target CI and record the exact supported compiler/platform matrix.

## Machine-readable record

The [`.github/project-ladder.v1.json`](https://github.com/Ivan-VHS/Reaper/blob/main/.github/project-ladder.v1.json) file is the repository-owned record. Update it in the same PR as a material change to project scope, runtime, integration boundaries or acceptance evidence. Promote only when the full cumulative gate is supported by source and reproducible verification.
