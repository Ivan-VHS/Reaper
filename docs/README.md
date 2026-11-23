> **Navigation:** Start with the [information architecture map](INFORMATION_ARCHITECTURE.md), then choose the relevant [topic hub](clusters/language-toolchain.md). The map catalogs every Markdown page and separates language, runtime, IDE, quality and integration contracts.

## Topic hubs

- [Language, compiler and runtime](clusters/language-toolchain.md) — Language semantics, parsing, intermediate representation, native execution and toolchain contracts.
- [Studio, IDE and user experience](clusters/studio-ide-ui.md) — Editor capabilities, LSP/DAP behavior, UI interaction, accessibility and visual documentation.
- [Architecture and system contracts](clusters/architecture-systems.md) — System decomposition, execution boundaries, runtime topology and architecture-level contracts.
- [Quality, validation and evidence](clusters/quality-evidence.md) — Engineering gates, diagnostics, repeatability, audits and evidence-backed status claims.
- [Integrations and project federation](clusters/federation-integration.md) — Plugin contracts, external runtimes, product interfaces and cross-project federation.
- [Planning, governance and reference material](clusters/planning-governance.md) — Roadmaps, catalogs, ownership, policy and supporting engineering references.

---

# Documentation

## Related OS product

[DuckOS — Mora application suite](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PREINSTALLED_APPLICATIONS.md) documents the seven applications provided by the OS layer. This is a related product reference only; it does not add app-suite capabilities to Reaper.

## Katyuhen ecosystem

[Integration with Katyuhen](KATYUHEN_INTEGRATION.md) records this project's ownership, registered interfaces, peer boundaries and validation requirements. The canonical federation registry is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/ecosystem/katyuhen.v1.json).

## Katyuhen ecosystem

[Integration with Katyuhen](KATYUHEN_INTEGRATION.md) records this project's ownership, registered interfaces, peer boundaries and validation requirements. The canonical federation registry is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/ecosystem/katyuhen.v1.json).

## Normative documentation standard

[Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) defines the shared terminology, capability maturity, runtime states, verification outcomes, evidence rules, localization requirements and documentation acceptance criteria. It is normative for this repository; project-specific architecture and implementation evidence remain authoritative for the product itself.

| File | Purpose |
|---|---|
| [VISUAL_DOCUMENTATION.md](VISUAL_DOCUMENTATION.md) | README graphics, SVG/raster assets, typography, Markdown/MDX, diagrams and rendering rules |
| [CODEX_66_SHOWCASE.md](CODEX_66_SHOWCASE.md) | native CODEX-66 browser, local completion/navigation and honest feature status |
| [IDE_666_IMPLEMENTATION.md](IDE_666_IMPLEMENTATION.md) | Studio IDE contract, canonical rule numbering and acceptance gates |
| [REAPER_IDE.md](REAPER_IDE.md) | LSP/DAP protocol services, shipped editor capabilities and limitations |
| [LSP_SEMANTIC_TOKENS.md](LSP_SEMANTIC_TOKENS.md) | LSP semantic token legend, encoding and lexical limits |
| [PROGRAM_CATALOG_1000.md](PROGRAM_CATALOG_1000.md) | adoption map, implementation status and verified first-wave capabilities |
| [NOO_TAH.md](NOO_TAH.md) | official Node.js runtime management, V8/libuv, npm, Inspector and Studio bridge |
| [KORA.md](KORA.md) | 66 standard-library functions in seven manifest-backed modules |
| [UI_MOTION.md](UI_MOTION.md) | accessible, persisted motion preferences and reduced-motion limits |
| [ANATIDAE_MOTION_CONSTITUTION.md](ANATIDAE_MOTION_CONSTITUTION.md) | shared white/blue/red desktop motion and surface profile |
| [PLUGINS.md](PLUGINS.md) | internal plugin host and extension lifecycle |
| [INTERNAL_PRODUCTS.md](INTERNAL_PRODUCTS.md) | integrated product catalogue and service contracts |
| [FEATURES.md](FEATURES.md) | shipped, reference and proposed capability matrix |
| [ARCHITECTURE.md](ARCHITECTURE.md) | runtime and compiler stages |
| [NATIVE_COMPILER.md](NATIVE_COMPILER.md) | checked scalar AOT compilation to C17 and the host toolchain |
| [NATIVE_COMPILER.md](NATIVE_COMPILER.md) | statically checked scalar AOT compilation to C17 and the host toolchain |
| [ENGINEERING.md](ENGINEERING.md) | quality, effect and release gates |
| [DIVISION_ENGINE.md](DIVISION_ENGINE.md) | checked division and workload allocation |
| [REAPER_813_FEATURE_ARCHITECTURE.md](REAPER_813_FEATURE_ARCHITECTURE.md) | proposal ID ranges and registry boundaries |
| [REAPER_PARSER_M1.md](REAPER_PARSER_M1.md) | native parser acceptance |
| [RUNTIME_PLATFORM.md](RUNTIME_PLATFORM.md) | Python runtime boundaries |
| [REAPER_UNIFIED_ARCHITECTURE.md](REAPER_UNIFIED_ARCHITECTURE.md) | native destination and language invariants |
| [MOST_LANGUAGE_SPEC.md](MOST_LANGUAGE_SPEC.md) | exact Russian aliases |
| [PROJECT_FEDERATION_MATRIX.md](PROJECT_FEDERATION_MATRIX.md) | peer-project boundaries and integrations |
| [THREADS_AND_FEDERATION.md](THREADS_AND_FEDERATION.md) | implementation and integration evidence |
| [ATOMIC_QUANTUM_133.md](ATOMIC_QUANTUM_133.md) | 133 stable operation IDs, eight tested classical simulation kernels and hardware boundary |
| [../LANGUAGE.md](../LANGUAGE.md) | syntax quick reference |
| [../editors/vscode/README.md](../editors/vscode/README.md) | editor grammar and external protocol-service notes |

Only tested behavior is labelled implemented. Registry counts are catalogued items, not feature-completion claims. Python remains the current compatibility reference; C17 parity requires separate conformance evidence.


## Motion and embedded graphics

[Motion Constitution v2026](MOTION_CONSTITUTION_V2026.md) is the shared source for timing/easing tokens, adaptive motion, reduced-motion precedence, themes, the 2×2/focus-scene lab layout, SVG/Canvas telemetry rules and the four-domain capability matrix. [UI_MOTION.md](UI_MOTION.md) records the native behavior implemented in this repository; planned showcase features are not reported as shipped.


## Bounded 500 UAH allocation reference

- [Multilingual specification](RESOURCE_ALLOCATION_500_UAH.md) — bounded budget model, scenarios and operating rules.
- [Offline interactive simulator](resource-allocation-500-uah.html) — adjust category amounts and see the remainder or overrun.
- [Example JSON](../examples/resource-allocation-500-uah.json) and [JSON Schema](../schemas/resource-allocation.v1.schema.json).

This is an illustrative personal-budgeting reference, not a claim that the host project manages payments or live retail prices.


## Language quality

[Language and editorial quality](LANGUAGE_QUALITY.md) — orthography, punctuation, lexical precision, syntax, multilingual review and conservative prose checks.


## Project-specific engineering profile

[IVAN_VHS_ENGINEERING_PROFILE.md](IVAN_VHS_ENGINEERING_PROFILE.md) translates the project's direction into concrete architecture boundaries, implementation priorities, human-readable code conventions and acceptance tests. It is a development contract; it does not mark planned work as implemented.


## Additional desktop profile

[Mora Amber design system](MORA_AMBER_DESIGN_SYSTEM.md) describes the shared warm palette and its contrast, material and motion constraints for the Reaper Studio workbench.
