# Reaper documentation

> **Documentation review:** 2026-11-27 UTC · **Reference runtime:** available · **Native C17 track:** partial

[English README](../README.md) · [Українська](../README.uk.md) · [Русский](../README.ru.md) · [简体中文](../README.zh-CN.md) · [Source](https://github.com/Ivan-VHS/Reaper) · [Issues](https://github.com/Ivan-VHS/Reaper/issues)

Start with a language-specific project README for the `.rpr` language, installation, validation-before-run workflow and current maturity boundaries.

## Key technical references

- [Features and maturity](FEATURES.md) — reference runtime versus native track.
- [Architecture](ARCHITECTURE.md) — compiler, runtime and service boundaries.
- [Native compiler](NATIVE_COMPILER.md) — partial C17 compiler and limited scalar AOT subset.
- [Hardware language track](HARDWARE_LANGUAGE.md) — checked hardware contracts and open work.
- [Runtime platform](RUNTIME_PLATFORM.md) — quotas, execution bounds and host effects.
- [Studio and IDE](REAPER_IDE.md) — editor and language-service boundaries.
- [Kora helpers](KORA.md) · [NOO TAH JavaScript boundary](NOO_TAH.md)
- [Implementation roadmap](IMPLEMENTATION_ROADMAP.md) — evidence-led gates.
- [Architecture 66](ARCHITECTURE_66.md) — architecture concept registry.

## Browse by topic

- [Language toolchain](clusters/language-toolchain.md) · [Architecture systems](clusters/architecture-systems.md)
- [Studio IDE and UI](clusters/studio-ide-ui.md) · [Quality evidence](clusters/quality-evidence.md)
- [Federation integration](clusters/federation-integration.md) · [Planning and governance](clusters/planning-governance.md)

## Shared engineering rules

- [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [Repository evolution directives](REPOSITORY_EVOLUTION_DIRECTIVES.md)

## Evidence and maturity

The Python reference runtime is the current behavioral baseline. Canonical IR and the selectable bytecode VM are implemented in that reference track; native C17 is partial and is not feature-equivalent. Runtime quotas are guardrails, not a security sandbox. Hardware descriptions do not automatically grant physical device access.

Describe behavior from source, build configuration, schemas, tests and CI evidence. Mark proposals and roadmap items as planned; do not infer compiler parity from a passing reference-runtime test.

**The index is navigation, not proof of implementation.**
