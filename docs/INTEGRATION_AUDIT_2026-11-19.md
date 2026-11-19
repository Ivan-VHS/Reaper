# Consolidated Reaper integration audit — 2026-11-19

This PR is a curated integration against the current `main` snapshot. Historical PRs and branches were inspected as evidence; their snapshots were not concatenated blindly.

## Baseline and policy

- Base branch: `main`
- Base commit: `9ec6a48213edadf23de96d00c641488a392a95dc` (the exact `main` base SHA recorded on PR #34)
- Keep the current mainline language/runtime and native C17 migration.
- Integrate compatible, tested slices; record prototype limits; never force-push or write directly to `main`.

## Included from existing work

| Source | Integrated scope |
|---|---|
| #10 | E2K host metadata detection, `--target-info`, tests and explicit native-codegen boundary |
| #15 | Modular compiler front end, deterministic Quarry IR, static checks, safe constant folding, bounded host APIs and their tests |
| #19 | MOST system architecture reference |
| #31 | HMGA v3 C17 catalogue: 20 axioms, 400 ordered descriptors, maximum 64 planning rounds and native C tests |
| #32 | HMGA v2 read-only repository auditor, tests and policy |
| #33 | Engineering standard, composition conformance tests and PR template |
| #12 | The current four-language README structure was retained and refreshed with a new source-aligned toolchain visual and the runtime systems diagram |

## Already present on main

The numeric-arithmetic guard from #29 is already present in `reaper/runtime.py`, and the zero-to-negative-power and complex-power regression tests already exist in `tests/test_language.py`. It is not duplicated.

The current tree already contains the core interpreter, native C17 lexer/parser/IR/optimizer/lowering/evolution foundation, feature registry, and its tests. These were preserved rather than replaced with older branch snapshots.

## Deliberately not concatenated

PR #14's monolithic `reaper/reaper_systems.py` and PR #16's alternate `actors/effects/epoch/profiling/relays/sentinel` modules overlap with the modular APIs selected from #15: resource regions, channels/actors, capability/effect context, routing, profiling, state snapshots and health policy. Copying all versions would create parallel implementations with competing APIs. This integration keeps the module-per-contract #15 set as the canonical prototype slice. The #14/#16 branches remain available for future selective review of genuinely unique behavior.

## Documentation and visuals

The English, Russian, Ukrainian and Simplified Chinese READMEs were updated. `assets/reaper-toolchain-preview.svg` is a source-aligned vector mockup of the CLI/IR path; `assets/reaper-nine-systems.svg` is the architecture diagram. Neither is a real screenshot captured from a running terminal. Sample terminal output is explicitly labelled illustrative.

The compiler front end emits portable Quarry IR. It does not generate machine code. The E2K profile reports host metadata only; MCST E2K native code generation remains unimplemented. Host APIs are opt-in Python integration primitives and do not become implicit language effects.

## Verification

New Python unit tests cover the compiler, compiler CLI, resource regions, checkpoint storage, local routing, asynchronous channels, capability permissions, profiling, interop, host-target reporting, composition and HMGA audit. New CTest coverage verifies HMGA v3 descriptor enumeration and finite-budget limits. CI additionally executes the compiler/runtime example and compiler CLI smoke path.

No local native build or local Python test result is claimed by this audit. The PR's GitHub Actions results remain authoritative.
