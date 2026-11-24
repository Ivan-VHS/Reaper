# Reaper documentation

The root [README](../README.md) is the product entry point: it summarizes the executable reference runtime, partial native track, local developer tools, requirements and first commands. Detailed contracts live in the topic documents below.

## Topic hubs

| Hub | Scope |
|---|---|
| [Language and toolchain](clusters/language-toolchain.md) | Syntax, type checking, interpreter, native compiler and embedded language |
| [Architecture and systems](clusters/architecture-systems.md) | Runtime layers, data flow, memory, hardware and system contracts |
| [Studio and IDE](clusters/studio-ide-ui.md) | Windows Studio, editor behavior, LSP/DAP and interaction |
| [Quality and evidence](clusters/quality-evidence.md) | Tests, validation, reproducibility, security and evidence |
| [Federation and integration](clusters/federation-integration.md) | NOO TAH, Kora, plugin and external project boundaries |
| [Planning and governance](clusters/planning-governance.md) | Maturity, decisions, roadmap and project standards |

## Security policy contract

[BAV policy runtime contract](BAV_POLICY_RUNTIME_CONTRACT.md) specifies Reaper's future deterministic/native policy-evaluation boundary for DuckOS BAV. It is a specification, not a shipped runtime.

## Start with the owning contract

- [Features](FEATURES.md) — current feature inventory and maturity.
- [Architecture](ARCHITECTURE.md) — implemented runtime structure and data flow.
- [Hardware Language](HARDWARE_LANGUAGE.md) — staged systems-language and hardware track.
- [Reaper IDE](REAPER_IDE.md) — Studio and language-tool boundaries.
- [NOO TAH](NOO_TAH.md) — Node.js process integration.
- [Kora](KORA.md) — optional standard-library helpers.
- [Contributing](../CONTRIBUTING.md) — local validation and review expectations.

## Repository map

~~~text
reaper/       Python reference runtime and developer tools
src/          partial native C17 implementation
include/      native public headers
tests/        runtime, protocol and native regression tests
examples/     reproducible .rpr programs
editors/      editor syntax support
docs/         architecture and capability contracts
~~~

Keep the reference runtime, partial native work and host-specific services separate in documentation. A registry/catalog entry is not proof of runtime implementation; source, tests and explicit maturity statements are authoritative.

## Implementation planning

- [Implementation roadmap](IMPLEMENTATION_ROADMAP.md) — evidence-based status and acceptance gates for the reference runtime, native C17 track, Studio, Jora and federation.
- [Feature matrix](FEATURES.md) — current capability surface and explicit limits.
