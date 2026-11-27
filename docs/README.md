# Reaper documentation

Start with the [project README](../README.md) for installation, first commands and current implementation status. The [documentation map](INFORMATION_ARCHITECTURE.md) links every topic area.

## Key pages
- [NEXUS system-service boundaries](NEXUS_SYSTEM_SERVICE_BOUNDARIES_V1.md) — service ownership and evidence limits.

- [Features and maturity](FEATURES.md)
- [Psychoporter Engineering Code function categories](FUNCTION_CATEGORIES_666.md)
- [Architecture](ARCHITECTURE.md)
- [Reaper System Features v1](REAPER_SYSTEM_FEATURES_V1.md) — ten bounded systems-language contracts and their implementation maturity.
- [System Features ADR](ADR_SYSTEM_FEATURES_V1.md) — native ABI decisions and language integration gates.
- [Snapshot integrity audit capability](SNAPSHOT_INTEGRITY_CAPABILITY.md) — bounded, read-only aggregate snapshot checks and transient no-persist comparison.
- [Snapshot integrity ADR](ADR_SNAPSHOT_INTEGRITY.md) — implementation scope and language-integration boundary.
- [Architecture foundation: 66 concepts](REAPER_ARCHITECTURE_FOUNDATION_66.md) — native C17 registry, nine architectural layers, dependency graph validation and deterministic ordering.
- [Foundational frameworks 1–5](FOUNDATIONAL_FRAMEWORKS_V1.md) — executable Reaper contracts for Framework frame, Platform, Environment, Infrastructure and Architecture.
- [Hardware language track](HARDWARE_LANGUAGE.md)
- [Processor Engineering Platform v1](PROCESSOR_ENGINEERING_PLATFORM.md) — processor project manifests, Pytyliki host evidence, target/ABI resource admission and the scalar-C17 host AOT workbench boundary.
- [Pytyliki Processor Fabric bridge v1](PYTYLIKI_PROCESSOR_FABRIC_BRIDGE.md) — PPF/evidence import, source-span preservation, typed resource ownership and separate processor backend gates.
- [Processor Fabric typed IR v1](PROCESSOR_FABRIC_TYPED_IR.md) — Reaper-owned type/effect/ownership binding and verified SemanticGraph sidecar; distinct from stack VM bytecode.
- [Processor Fabric typed IR v1](PROCESSOR_FABRIC_TYPED_IR.md) — Reaper-owned type/effect/ownership binding and verified SemanticGraph sidecar; distinct from stack VM bytecode.
- [Typed Registry v1](TYPED_REGISTRY.md) — Reaper-native type, layout, platform, ABI, effect and capability contracts.
- [System Runtime ABI v1](SYSTEM_RUNTIME_ABI_V1.md)
- [DABI64 Desktop Host v1](DABI64_DESKTOP_HOST_V1.md)
- [Implementation roadmap](IMPLEMENTATION_ROADMAP.md)
- [50,000-line Reaper-native expansion plan](NATIVE_REAPER_EXPANSION_50000.md)
- [Studio and IDE](REAPER_IDE.md)
- [Mora archive contracts](MORA_ARCHIVE_CONTRACTS.md) — executable `.rpr` validators, record layouts, provenance rules and offline regression fixture.
- [Early mathematics contracts](EARLY_MATH_CONTRACTS.md) — cardinality, one-to-one pairing, lossless partitions, balanced sharing and number composition.
- [NEXUS federation profile](NEXUS_FEDERATION_PROFILE_V1.md) — Reaper ownership, peer contracts and compatibility boundaries.

## Browse by topic

- [Language and toolchain](clusters/language-toolchain.md)
- [Psychoporter Engineering Code function categories](FUNCTION_CATEGORIES_666.md)
- [Architecture and systems](clusters/architecture-systems.md)
- [Studio and IDE](clusters/studio-ide-ui.md)
- [Quality and evidence](clusters/quality-evidence.md)
- [Federation and integration](clusters/federation-integration.md)
- [Planning and governance](clusters/planning-governance.md)

## Shared rules

- [Psychoporter Engineering Code coding and human-layer standard](PSYCHOPORTER_666.md)
- [Documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [Repository evolution directives](REPOSITORY_EVOLUTION_DIRECTIVES.md)

Treat the Python reference runtime, native compiler track, System Runtime host ABI and privileged hardware work as separate maturity levels. Source, tests and CI are the evidence for implemented behavior.

- [OPlague GPU telemetry v1 ingestion](OPLAGE_GPU_TELEMETRY.md)

- [System Functions v1](SYSTEM_FUNCTIONS.md) — bounded runtime APIs, guarantees and implementation limits.
