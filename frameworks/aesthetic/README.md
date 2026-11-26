# Reaper Aesthetic & Architecture Evolution Framework

**Short name:** RAAEF  
**Language:** Reaper  
**Version:** 1.0.0  
**Maturity:** Genesis — source foundation present; runtime and CI evidence pending

RAAEF treats a visual system as a typed program rather than a loose collection of theme values. A profile is validated by Vorke, expanded into HIR by LejjyFish, normalized into MIR by Lejjy, and lowered by Oplos into a target-specific LIR plan. Holmosaptimu exposes this pipeline to Reaper programs. Sentan, Cellene, Kolir and SOMO add architecture, design and source-evolution planning.

## Framework family

| Framework | Responsibility | Canonical source |
|---|---|---|
| Vorke | Tagged nominal types, profile contracts and invariants | [engine/vorke.rpr](engine/vorke.rpr) |
| Jellymeat | Versioned profile catalogue | [engine/jellymeat.rpr](engine/jellymeat.rpr) |
| LejjyFish | High-level design IR | [engine/lejjyfish.rpr](engine/lejjyfish.rpr) |
| Lejjy | HIR normalization and MIR | [engine/lejjy.rpr](engine/lejjy.rpr) |
| Oplos | Target-specific LIR lowering | [engine/oplos.rpr](engine/oplos.rpr) |
| Holmosaptimu | Reaper profile compiler adapter | [engine/holmosaptimu.rpr](engine/holmosaptimu.rpr) |
| Sentan | Architecture graph and cycle validation | [engine/sentan.rpr](engine/sentan.rpr) |
| Cellene | Design assessment and profile evolution proposals | [engine/cellene.rpr](engine/cellene.rpr) |
| Kolir | Bounded source change plans | [engine/kolir.rpr](engine/kolir.rpr) |
| SOMO | Observe/propose orchestration | [engine/somo.rpr](engine/somo.rpr) |

The stable import surface is [all.rpr](all.rpr). The central discovery index is [frameworks/catalog.v1.json](../catalog.v1.json).

## Compiler pipeline

    AestheticProfile
        -> Vorke validation
        -> LejjyFish / AestheticHIR
        -> Lejjy / AestheticMIR
        -> Oplos / AestheticLIR
        -> target renderer adapter

- HIR preserves semantic intent: canvas, surfaces, typography, layout, motion and accessibility roles.
- MIR normalizes profile values into deterministic property operations and resolves reduced-motion preferences.
- LIR lowers those operations to target-facing style and motion instructions.
- The current LIR is a declarative render plan. It does not call a native widget toolkit or draw to a GPU surface.

The profile IR remains a domain-specific Reaper pipeline. The native C17 core now provides a shared typed HIR/MIR/LIR API covering bounded scalar expressions plus aesthetic property nodes, and emits a deterministic C17 instruction table. It is not full Reaper grammar parity: parser-to-HIR lowering for imported modules, collections, control flow, effects and native runtime calls remains incomplete. Consequently, this does not yet compile the full RAAEF .rpr module family to native code.

## Typed profile contract

Vorke uses versioned tagged tuples with fixed field positions. JSON Schema contracts define the external interchange format; the Reaper validators enforce the runtime boundary. The source request requires a canonical `sha256:` plus 64-hex digest shape, but only the future repository adapter can verify that digest against a real Git object. This is a nominal runtime contract, not first-class structure, enum, generic or ownership syntax in Reaper.

The profile shape is:

1. AestheticProfile tag, schema version, profile ID
2. Target: platform, renderer and scale
3. Palette: twelve semantic color roles
4. Typography: family, monospace family, base size, scale ratio, body and heading weights, line height
5. Layout: grid, spacing, radius and density
6. Motion: reduced-motion flag, fast, standard and slow durations, easing token
7. Accessibility: minimum contrast target, visible focus, keyboard navigation and reduced-motion support

Contracts: [profile schema](schemas/profile.v1.schema.json), [design IR schema](schemas/design-ir.v1.schema.json), [architecture graph schema](schemas/architecture-graph.v1.schema.json), [source evolution request schema](schemas/source-evolution-request.v1.schema.json).

## Automatic evolution loop

SOMO coordinates a deterministic pipeline and consults the PLAGUE v1 action policy before analysis or planning:

1. Validate the requested mode through PLAGUE's default-deny action policy.
2. Validate the current and target aesthetic profiles.
3. Compile the baseline profile through HIR, MIR and LIR.
4. Assess the target design against the declared accessibility contract.
5. Validate both current and proposed architecture graphs, check that node dependency declarations match graph edges, reject cycles, and compute an explicit architecture delta.
6. In `observe`, return evidence and graph comparisons without generating source-change plans.
7. In `propose`, generate bounded Cellene/Kolir proposals only after the PLAGUE plan capability is allowed; defer changes whose declared risk is not lower than their expected benefit.
8. Return the profile compile products, architecture delta and source plan as a reviewable proposal.

Observe performs assessment only. Propose emits a bounded change plan. A native C17 transactional apply engine now defines SHA-256-pinned whole-file patch descriptors, signed repository/path grant callbacks, exact Git revision verification, an isolated workspace, sandboxed registered checks, atomic topic-branch publication, durable audit and conditional rollback/recovery callbacks. The engine fails closed without every host capability. However, concrete Windows/POSIX Git/workspace and sandbox adapters, plus a Reaper-to-native bridge, are not yet available. SOMO therefore continues to block apply. The system never treats account repository visibility as write authorization. PLAGUE's current Reaper module is an action-policy matrix, not the cryptographic host grant implementation.

## Example

See [examples/pipeline_smoke.rpr](examples/pipeline_smoke.rpr). It loads the DAK Noir and Mora Studio profiles, compiles the baseline, checks an acyclic module graph and builds an evolution proposal.

## Maturity and limitations

Implemented source slices are listed in [manifest.v1.json](manifest.v1.json). The current Cellene assessment checks declared focus, keyboard-navigation and reduced-motion requirements; it does not calculate actual foreground/background contrast ratios or compare rendered screenshots. This increment does not claim native C17 support for aesthetic modules, visual-regression tooling, live theme switching, source patch application, privileged host effects, automatic PR creation, automatic merging or release.

The native CTest suite now includes typed compiler IR, SHA-256, generated-C17 compilation and in-memory transaction-host scenarios. These tests are wired into the native CMake build but their CI result must be observed before the work can be marked verified. The original Reaper smoke program and its runtime CI also remain subject to the separate RAAEF PR checks. The in-memory host is not evidence that a real Git or OS sandbox adapter is secure.
