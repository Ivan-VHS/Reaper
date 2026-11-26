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

The profile IR is a domain-specific compiler pipeline implemented in Reaper. It is not yet the general-purpose HIR/MIR/LIR of the Reaper source-language compiler. In particular, it does not extend the experimental scalar C17 backend, which currently lacks module and collection support.

## Typed profile contract

Vorke uses versioned tagged tuples with fixed field positions. JSON Schema contracts define the external interchange format; the Reaper validators enforce the runtime boundary. This is a nominal runtime contract, not first-class structure, enum, generic or ownership syntax in Reaper.

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
2. Compile the baseline profile through HIR, MIR and LIR.
3. Assess the target design against the declared accessibility contract.
4. Validate the architecture graph and dependency acyclicity.
5. Generate a bounded Kolir plan for architecture, design, compiler, source, tests and documentation work.
6. Return a proposal with evidence-bearing outputs for review.

Observe performs assessment only. Propose emits a bounded change plan. Apply is intentionally blocked until repository grants, path allowlists, revision pinning, patch application, isolated checks, immutable audit and tested rollback are implemented. The system never treats an account's repository visibility as write authorization. PLAGUE currently provides an action-policy matrix, not authenticated repository grants or path-level authorization.

## Example

See [examples/pipeline_smoke.rpr](examples/pipeline_smoke.rpr). It loads the DAK Noir and Mora Studio profiles, compiles the baseline, checks an acyclic module graph and builds an evolution proposal.

## Maturity and limitations

Implemented source slices are listed in [manifest.v1.json](manifest.v1.json). This increment does not claim native C17 support for aesthetic modules, visual-regression tooling, live theme switching, source patch application, privileged host effects, automatic PR creation, automatic merging or release.

The smoke source has been added but has not yet been executed by a Reaper runtime in this session. JSON schemas and CI wiring also remain pending validation. These limitations are part of the contract, not hidden roadmap footnotes.
