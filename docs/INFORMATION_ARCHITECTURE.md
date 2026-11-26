# Documentation information architecture

[Project README](../README.md) · [Documentation index](README.md)

This is the canonical navigation map for Reaper. The root README is the entry point, this page is the documentation pillar, and the topic hubs organize the language, runtime, Studio and federation material into coherent clusters.

## Navigation model

- **Entry point:** root README describes product scope and supported workflows.
- **Pillar:** this map defines the documentation clusters and catalogs every Markdown page.
- **Topic hubs:** each hub lists its documents and provides a contextual path through related contracts.
- **Authority:** implementation claims remain grounded in source, tests and schemas; plans are not shipped features.

## Topic hubs

- [Language, compiler and runtime](clusters/language-toolchain.md) — Language semantics, parsing, intermediate representation, native execution and toolchain contracts.
- [Studio, IDE and user experience](clusters/studio-ide-ui.md) — Editor capabilities, LSP/DAP behavior, UI interaction, accessibility and visual documentation.
- [Architecture and system contracts](clusters/architecture-systems.md) — System decomposition, execution boundaries, runtime topology and architecture-level contracts.
- [Quality, validation and evidence](clusters/quality-evidence.md) — Engineering gates, diagnostics, repeatability, audits and evidence-backed status claims.
- [Integrations and project federation](clusters/federation-integration.md) — Plugin contracts, external runtimes, product interfaces and cross-project federation.
- [Planning, governance and reference material](clusters/planning-governance.md) — Roadmaps, catalogs, ownership, policy and supporting engineering references.

## Cross-repository boundaries

The neighboring projects have distinct responsibilities. Shared vocabulary or integration references do not imply a shared runtime, ABI or release lifecycle.

- [Pytyliki documentation map](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/INFORMATION_ARCHITECTURE.md) — processor-system workstation and bounded C11 modules.
- [OPlague documentation map](https://github.com/Ivan-VHS/OPlague/blob/main/docs/INFORMATION_ARCHITECTURE.md) — read-only device and driver inspection.
- [VentuSample documentation map](https://github.com/Ivan-VHS/VentuSample/blob/main/docs/INFORMATION_ARCHITECTURE.md) — procedural audio and DSP workstation.
- [DuckOS documentation map](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/INFORMATION_ARCHITECTURE.md) — repository entry-point map.

## Full document catalog

Each Markdown page is linked here and from its topic hub, giving readers more than one meaningful inbound route. The cluster description supplies context; anchors use the target document's name.

### Language, compiler and runtime

- [HARDWARE LANGUAGE](HARDWARE_LANGUAGE.md)
- [C MIGRATION](C_MIGRATION.md)
- [CONCATENATION ARCHITECTURE](CONCATENATION_ARCHITECTURE.md)
- [FORMATTER AND TOOLCHAIN](FORMATTER_AND_TOOLCHAIN.md)
- [KORA](KORA.md)
- [LANGUAGE QUALITY](LANGUAGE_QUALITY.md)
- [LSP SEMANTIC TOKENS](LSP_SEMANTIC_TOKENS.md)
- [MOST 147 FEATURE REGISTRY](MOST_147_FEATURE_REGISTRY.md)
- [MOST 400 COMBINATORIAL MATRIX](MOST_400_COMBINATORIAL_MATRIX.md)
- [MOST FUNCTIONS 666](MOST_FUNCTIONS_666.md)
- [FUNCTION CATEGORIES 666](FUNCTION_CATEGORIES_666.md)
- [MOST IMPLEMENTATION STATUS](MOST_IMPLEMENTATION_STATUS.md)
- [MOST LANGUAGE SPEC](MOST_LANGUAGE_SPEC.md)
- [MOST RUSSIAN 66 RULES](MOST_RUSSIAN_66_RULES.md)
- [MOST RUSSIAN NATIVE PROFILE](MOST_RUSSIAN_NATIVE_PROFILE.md)
- [NATIVE IR EXECUTION](NATIVE_IR_EXECUTION.md)
- [POLYGLOT CODE](POLYGLOT_CODE.md)
- [POLYGLOT IMMERSION](POLYGLOT_IMMERSION.md)
- [QCS FRONTEND](QCS_FRONTEND.md)
- [REAPER PARSER M1](REAPER_PARSER_M1.md)
- [RUNTIME PLATFORM](RUNTIME_PLATFORM.md)
- [SELF HOSTING BOOTSTRAP](SELF_HOSTING_BOOTSTRAP.md)
- [TOKEN CATALOG](TOKEN_CATALOG.md)
- [LANGUAGE](../LANGUAGE.md)

### Studio, IDE and user experience

- [ANATIDAE MOTION CONSTITUTION](ANATIDAE_MOTION_CONSTITUTION.md)
- [CODEX 66 SHOWCASE](CODEX_66_SHOWCASE.md)
- [IDE 666 IMPLEMENTATION](IDE_666_IMPLEMENTATION.md)
- [MOTION CONSTITUTION V2026](MOTION_CONSTITUTION_V2026.md)
- [REAPER IDE](REAPER_IDE.md)
- [REAPER TOOLCHAIN EVOLUTION IDE](REAPER_TOOLCHAIN_EVOLUTION_IDE.md)
- [UI MOTION](UI_MOTION.md)
- [UI UX 2026 CONVERGENCE](UI_UX_2026_CONVERGENCE.md)
- [UI UX ATLAS 2026](UI_UX_ATLAS_2026.md)
- [UI UX CODEX 40026](UI_UX_CODEX_40026.md)
- [UI UX SYSTEM](UI_UX_SYSTEM.md)
- [VISUAL DOCUMENTATION](VISUAL_DOCUMENTATION.md)

### Architecture and system contracts

- [HARDWARE LANGUAGE](HARDWARE_LANGUAGE.md)
- [ARCHITECTURE 66](ARCHITECTURE_66.md)
- [REAPER ARCHITECTURE FOUNDATION 66](REAPER_ARCHITECTURE_FOUNDATION_66.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [ATOMIC QUANTUM 133](ATOMIC_QUANTUM_133.md)
- [CLINICAL SYSTEMS CSR120](CLINICAL_SYSTEMS_CSR120.md)
- [CONSTITUTION 666 PROFILE](CONSTITUTION_666_PROFILE.md)
- [DISTRIBUTED SYSTEMS ENGINEERING STANDARD](DISTRIBUTED_SYSTEMS_ENGINEERING_STANDARD.md)
- [DIVISION DECOMPOSITION ENGINE](DIVISION_DECOMPOSITION_ENGINE.md)
- [DIVISION ENGINE](DIVISION_ENGINE.md)
- [NATIVE CAPABILITY SUITE](NATIVE_CAPABILITY_SUITE.md)
- [REAPER 813 FEATURE ARCHITECTURE](REAPER_813_FEATURE_ARCHITECTURE.md)
- [REAPER UNIFIED ARCHITECTURE](REAPER_UNIFIED_ARCHITECTURE.md)
- [TRANSACTIONAL RUNTIME](TRANSACTIONAL_RUNTIME.md)
- [UNIFIED PROJECT CONTRACT](UNIFIED_PROJECT_CONTRACT.md)

### Quality, validation and evidence

- [CHINESE PROVERBS 100 ENGINEERING CROSSWALK](CHINESE_PROVERBS_100_ENGINEERING_CROSSWALK.md)
- [DOCUMENTATION CONTROL](DOCUMENTATION_CONTROL.md)
- [ENGINEERING EVOLUTION FRAMEWORK](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [ENGINEERING](ENGINEERING.md)
- [DIAGNOSTICS](errors/DIAGNOSTICS.md)
- [EXECUTION AUDIT](EXECUTION_AUDIT.md)
- [IVAN VHS ENGINEERING PROFILE](IVAN_VHS_ENGINEERING_PROFILE.md)
- [PROJECT STEWARDSHIP STANDARD](PROJECT_STEWARDSHIP_STANDARD.md)
- [QUALITY COMMERCIAL STANDARD](QUALITY_COMMERCIAL_STANDARD.md)
- [QUALITY REMEDIATION STANDARD](QUALITY_REMEDIATION_STANDARD.md)
- [QUALITY REPEATABILITY NATIVE](QUALITY_REPEATABILITY_NATIVE.md)
- [THESIS ASSERTION GRAPH](THESIS_ASSERTION_GRAPH.md)
- [UNIFIED ENGINEERING STANDARD](UNIFIED_ENGINEERING_STANDARD.md)

### Integrations and project federation

- [FEDERATED INTEGRATION](FEDERATED_INTEGRATION.md)
- [INTERNAL PRODUCT ECOSYSTEM](INTERNAL_PRODUCT_ECOSYSTEM.md)
- [INTERNAL PRODUCTS](INTERNAL_PRODUCTS.md)
- [NOO TAH](NOO_TAH.md)
- [OCTA PYRAMID FEDERATION](OCTA_PYRAMID_FEDERATION.md)
- [PLUGINS](PLUGINS.md)
- [PROJECT FEDERATION MATRIX](PROJECT_FEDERATION_MATRIX.md)
- [REPLACEMENT TOOLS](REPLACEMENT_TOOLS.md)
- [REPORT ENVELOPE](REPORT_ENVELOPE.md)
- [THREADS AND FEDERATION](THREADS_AND_FEDERATION.md)

### Planning, governance and reference material

- [CONTRIBUTING](../CONTRIBUTING.md)
- [DUCK SOVEREIGN CANON](DUCK_SOVEREIGN_CANON.md)
- [EMBEDDED C WORKBENCH](EMBEDDED_C_WORKBENCH.md)
- [FEATURES](FEATURES.md)
- [HUMAN FIRST GOVERNANCE](HUMAN_FIRST_GOVERNANCE.md)
- [IMPLEMENTATION UPDATE 2026 11 20](IMPLEMENTATION_UPDATE_2026-11-20.md)
- [IMPROVEMENT CONFLICT STANDARD](IMPROVEMENT_CONFLICT_STANDARD.md)
- [MICROBUDGET PLANNER](MICROBUDGET_PLANNER.md)
- [ORTHOGONAL METRIC ENGINE](ORTHOGONAL_METRIC_ENGINE.md)
- [PROGRAM CATALOG 1000](PROGRAM_CATALOG_1000.md)
- [REAPER AUTONOMOUS EVOLUTION](REAPER_AUTONOMOUS_EVOLUTION.md)
- [REAPER EVOLUTION ENGINE](REAPER_EVOLUTION_ENGINE.md)
- [RESOURCE ALLOCATION 500 UAH](RESOURCE_ALLOCATION_500_UAH.md)
- [SELF PRODUCT COMPOSITION](SELF_PRODUCT_COMPOSITION.md)
- [SEMANTIC HYPERGRAPH AND SOURCE MAP](SEMANTIC_HYPERGRAPH_AND_SOURCE_MAP.md)
- [UNIFIED DOCUMENTATION STANDARD](UNIFIED_DOCUMENTATION_STANDARD.md)
- [README](../editors/vscode/README.md)
- [ANATIDAE NAMING CANON](../federation/ANATIDAE_NAMING_CANON.md)
- [README](../README.md)
- [README.Ru](../README.ru.md)
- [README.Uk](../README.uk.md)
- [README.Zh CN](../README.zh-CN.md)
- [SECURITY](../SECURITY.md)

## Maintenance contract

A new page must be added to its topic hub and this catalog in the same change, and receive at least two useful incoming paths. Keep important pages within three to four clicks of the root README. Use direct relative links within this repository and canonical HTTPS links across repositories. Avoid vague anchors, duplicate targets for competing concepts, broken links and repetitive link blocks.
