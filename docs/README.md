# Reaper documentation

**Documentation baseline:** 2026-11-26 · **Project status:** alpha / multiple implementation tracks.

Start with the [root README](../README.md) for the language/runtime boundary, build commands and current limitations. The [Information Architecture](INFORMATION_ARCHITECTURE.md) page catalogs the complete documentation library.

## Core references

- [Features and maturity](FEATURES.md)
- [Architecture](ARCHITECTURE.md)
- [Architecture foundation: 66 concepts](REAPER_ARCHITECTURE_FOUNDATION_66.md) — native registry, nine semantic layers and bounded dependency graph validation.
- [Runtime platform and quotas](RUNTIME_PLATFORM.md)
- [Native compiler](NATIVE_COMPILER.md)
- [Hardware language track](HARDWARE_LANGUAGE.md)
- [Canonical IR execution](NATIVE_IR_EXECUTION.md)
- [System Runtime ABI v1](SYSTEM_RUNTIME_ABI_V1.md)
- [DABI64 Desktop Host v1](DABI64_DESKTOP_HOST_V1.md)
- [Studio and IDE](REAPER_IDE.md)
- [Diagnostics](errors/DIAGNOSTICS.md)
- [Federated integration](FEDERATED_INTEGRATION.md)
- [Unified project contract](UNIFIED_PROJECT_CONTRACT.md)

## Browse by topic

- [Language and toolchain](clusters/language-toolchain.md)
- [Studio, IDE and UI](clusters/studio-ide-ui.md)
- [Architecture and system contracts](clusters/architecture-systems.md)
- [Quality and evidence](clusters/quality-evidence.md)
- [Federation and integration](clusters/federation-integration.md)
- [Planning and governance](clusters/planning-governance.md)

## Shared standards

- [Canonical documentation and publication standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [Unified engineering standard](UNIFIED_ENGINEERING_STANDARD.md)
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [Repository evolution directives](REPOSITORY_EVOLUTION_DIRECTIVES.md)
- [Contribution guide](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)

## Evidence rule

The Python reference runtime, native C17 implementation, hardware adapter contracts and self-hosting frontend are separate maturity levels. Source and tests prove only the paths they exercise. Resource quotas are not a sandbox, an MMIO descriptor is not a physical mapping, and a feature registry is not compiler completeness.
