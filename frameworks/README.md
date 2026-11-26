# Reaper framework registry

This directory is the discovery point for the framework families currently identified in the Reaper repository and its active implementation PRs.

- [Machine-readable catalogue](catalog.v1.json)
- [Catalogue JSON Schema](catalog.v1.schema.json)
- [RAAEF: typed aesthetic profiles and evolution](aesthetic/README.md)

## Registry inventory

**Important:** an open PR is not part of `main`. A draft PR is not merge-ready. The catalogue records source branch, base branch, dependency and implementation boundary so the families can be integrated without pretending that proposed code has shipped.

| Family | Purpose | Current review state |
|---|---|---|
| [RAAEF](aesthetic/README.md) | Typed aesthetic profiles, HIR/MIR/LIR, architecture/design/source evolution planning | [#364 — draft, stacked on #358](https://github.com/Ivan-VHS/Reaper/pull/364) |
| Native Typed IR and Apply Engine | Shared C17 HIR/MIR/LIR, SHA-256 patch descriptors and guarded isolated topic-branch apply contract | [#382 — draft, stacked on #364](https://github.com/Ivan-VHS/Reaper/pull/382) |
| AESTHETICA | Evidence-based aesthetic evaluation on independent beauty and ugliness axes | [#360 — open](https://github.com/Ivan-VHS/Reaper/pull/360) |
| Repository Engineering 66 | Native registry of 66 repository-engineering profiles with evidence gates | [#363 — open](https://github.com/Ivan-VHS/Reaper/pull/363) |
| Foundational Five | Scaffold, Platform, Environment, Infrastructure and Architecture contracts | [#362 — open](https://github.com/Ivan-VHS/Reaper/pull/362) |
| Eight Reaper Modules | GalHero, Call-and-Back, Stacked Options, PerenosiMOST/MOST, Blau, Shashio and Showel Fleppery CODE | [#336 — open](https://github.com/Ivan-VHS/Reaper/pull/336) |
| Native Framework Core | C17 manifests, ABI/dependency checks, capability grants and lifecycle rollback | [#335 — open](https://github.com/Ivan-VHS/Reaper/pull/335) |
| Framework Federation 20 | Twenty namespaced framework contracts with a bounded C ABI registry | [#333 — open](https://github.com/Ivan-VHS/Reaper/pull/333) |
| Federation 120 Handlers | Reaper reference-runtime handlers on top of the 20-namespace registry | [#356 — draft, depends on #333](https://github.com/Ivan-VHS/Reaper/pull/356) |
| PLAGUE | Repository evolution policy, bounded proposal assessment and review selection | [#358 — draft](https://github.com/Ivan-VHS/Reaper/pull/358) |
| RForge Specification | Multi-product family and archetype contracts | [#354 — draft](https://github.com/Ivan-VHS/Reaper/pull/354) |
| RForge Reaper Modules | Twenty Reaper reference-runtime framework archetypes | [#357 — draft, depends on #354](https://github.com/Ivan-VHS/Reaper/pull/357) |
| Rivet | Framework/multitool capability composition planner | [#355 — draft](https://github.com/Ivan-VHS/Reaper/pull/355) |
| ДОМ Runtime Foundation | Canonical application/system runtime architecture | [#350 — draft](https://github.com/Ivan-VHS/Reaper/pull/350) |
| ДОМ Native Foundation Slice | Initial Reaper source implementation on top of the framework modules | [#353 — draft, depends on #336](https://github.com/Ivan-VHS/Reaper/pull/353) |

The inventory contains **15 registered family lines**. The 66-profile registry and 20-namespace federation each contain many individual entries; they are not counted as 66 or 20 separate repository PRs.

## Integration order

1. Review the framework core and Reaper module foundations for stable ABI and source conventions.
2. Resolve framework federation and its dependent handler PR.
3. Resolve PLAGUE foundation before the stacked RAAEF PR; then retarget RAAEF to `main` after the base is integrated.
4. Resolve the RForge specification before its implementation modules.
5. Resolve the eight-module foundation before the ДОМ native slice.
6. Keep AESTHETICA as a complementary evaluator. RAAEF's typed visual profile compiler should consume its explainable evaluation outputs through a versioned adapter rather than duplicate its scoring engine.

The registry is an integration map, not a bulk merge instruction. Each PR still requires its declared tests, CI, review and dependency reconciliation.

## Safety and maturity rules

- A catalogue entry proves discoverability only, not implementation maturity.
- No framework gains host or repository authority from its manifest.
- Source mutation must be separately granted, path-scoped, revision-pinned and audited.
- Apply operations require an isolated allowlisted runner, measured limits and tested rollback.
- Merge, release, deployment, secret access and untrusted command execution remain separate capabilities.
- Conflicting framework responsibilities must be resolved through explicit ownership and versioned contracts, not by creating duplicate runtimes, schedulers or registries.
