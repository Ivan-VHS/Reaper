# Reaper documentation

Start with the [project README](../README.md) for installation, first commands and current implementation status.

## Language authority

- [Reaper Language Canon v1](LANGUAGE_CANON.md) — normative syntax, semantics, profiles, compiler boundaries and conformance rules.
- [Language quick reference](../LANGUAGE.md) — concise syntax and examples.
- [Machine-readable language contract](../language/language-canon.v1.json) — versioned contract projection and implementation status.
- [МОСТ language profile](MOST_LANGUAGE_SPEC.md) — exact Russian aliases over canonical Reaper tokens.

The language canon is authoritative for syntax and semantics. Other documents may explain implementation or propose future work, but MUST NOT define competing keywords, operators or runtime meaning.

## Key pages

- [Features and maturity](FEATURES.md)
- [Architecture](ARCHITECTURE.md)
- [Unified language architecture](REAPER_UNIFIED_ARCHITECTURE.md)
- [Hardware language track](HARDWARE_LANGUAGE.md)
- [Native compiler](NATIVE_COMPILER.md)
- [Implementation roadmap](IMPLEMENTATION_ROADMAP.md)
- [Studio and IDE](REAPER_IDE.md)

## Browse by topic

- [Language and toolchain](clusters/language-toolchain.md)
- [Architecture and systems](clusters/architecture-systems.md)
- [Studio and IDE](clusters/studio-ide-ui.md)
- [Quality and evidence](clusters/quality-evidence.md)
- [Federation and integration](clusters/federation-integration.md)
- [Planning and governance](clusters/planning-governance.md)

## Shared rules

- [Psychoporter 666 coding and human-layer standard](PSYCHOPORTER_666.md)
- [Documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [Repository evolution directives](REPOSITORY_EVOLUTION_DIRECTIVES.md)

Treat the Python reference runtime, native compiler track and privileged hardware work as separate maturity levels. Source, tests and CI are the evidence for implemented behavior.
