# Reaper implementation roadmap

**Reviewed:** 2026-11-26  
**Authority:** source code, tests, build configuration and required CI checks.  
**Product boundary:** Reaper is an executable Python reference language and local developer workbench with a partial native C17 track. It is not currently a complete native compiler, kernel runtime or unrestricted hardware execution environment.

## Status vocabulary

| State | Meaning | Exit evidence |
|---|---|---|
| Delivered | The scoped behavior exists in source and its regression checks pass | Source path, test and green required CI context |
| Partial | A bounded subset exists, but the broader capability is incomplete | Exact implemented subset, explicit exclusions and next acceptance test |
| Planned | No production implementation exists yet | Owner/dependency, security model, design decision and executable acceptance criteria |
| Not applicable | The product has no such runtime surface | Rationale and product boundary; no empty placeholder feature |

Never move a row to Delivered because a registry, design, README, schema or generated scaffold exists.

## Current baseline

| Track | Current state | Main evidence |
|---|---|---|
| Python language | Delivered compatibility baseline: lexer, parser, interpreter, modules, CLI and REPL | `reaper/`, `tests/`, `examples/` |
| Resource controls | Delivered reference-runtime quotas and explicit audit/effect boundaries | Runtime source and quota/security regression tests |
| Static analysis | Partial conservative type and call diagnostics | `reaper --check`, Studio and LSP tests |
| Studio | Delivered Windows editor/debugger foundation | `reaper_desktop.py`, desktop workflow |
| LSP/DAP | Delivered stdio protocol subsets with documented limits | Protocol modules and protocol tests |
| NOO TAH | Process-isolated Node.js integration through the installed upstream Node runtime | NOO TAH implementation and compatibility workflow |
| Native C17 | Partial lexer/parser/AST/checked-i64 IR/limited lowering | `src/`, `include/`, `tests/`, native C workflow |
| Native MMIO | Descriptor validation and callback contract only | Native headers, source and negative tests |
| Jora factory | Deterministic request validation, catalogue/composition and scaffold generation | `docs/JORA_APPLICATION_FACTORY.md`, CLI tests; generated packs remain non-installable |
| Federation | Versioned metadata/adapters for OPlague, VentuSample and optional Pytyliki ABI | Federation manifests and integration tests |
| МОСТ | 21 executable aliases and 33 reserved aliases | `docs/MOST_IMPLEMENTATION_STATUS.md`, registry validator |\n| Framework programme | 330 Reaper `.rpr` modules: 5 in batch 01 and 325 indexed modules across domains 02–66 | `reaper/frameworks/`, `framework-index.v1.json`, `tests/test_framework_programme.py`; feature branch CI pending |

## Workstreams and acceptance gates

### R1 — Preserve reference-runtime correctness

**Status: Delivered baseline; continuous maintenance.**

- Keep parsing, tree-walk execution and VM execution behaviorally aligned.
- Preserve bounded source size, token counts, execution steps, call depth, collection/text/heap growth and open handles.
- Make host effects explicit, capability-gated and auditable.
- Add regression tests for every language semantic or quota change.

**Acceptance:** Python 3.10, 3.11 and 3.12 CI pass; reference/VM parity tests pass; examples validate; no test bypasses a runtime quota.

### R2 — Complete the language contract before expanding syntax

**Status: Partial.**

- Maintain one normative grammar and specify evaluation order, scope, mutability, errors and module resolution.
- Define source locations and diagnostic stability for Unicode, CRLF and multi-file inputs.
- Extend type analysis only where sound conservative inference is possible; unknown must remain unknown rather than guessed.
- Specify serialization and compatibility for the AST/IR.

**Acceptance:** grammar fixtures, parser negative cases, stable diagnostics, cross-engine conformance cases and migration notes pass on all supported Python versions.

### R3 — Native C17 compiler track

**Status: Partial; native backend and self-hosting are not delivered.**

1. Freeze a versioned native IR contract and verify all node kinds, operands, control-flow targets, definitions, types and call arities.
2. Complete deterministic symbol resolution and module/import validation.
3. Implement lowering for the explicitly supported language subset, with checked overflow and defined error behavior.
4. Build one host-native executable path with a documented ABI and no implicit dynamic loading.
5. Add reference-runtime/native parity fixtures for every supported construct.
6. Add reproducible builds, sanitizers and target-specific CI before expanding the language subset.

**Acceptance:** a declared subset compiles and runs from source to native executable; each fixture produces the same observable result/error as the reference runtime; malformed IR is rejected before code generation. Full-language parity remains Partial until every normative language construct is covered.

### R4 — Native runtime, memory and host effects

**Status: Planned beyond the current checked API contracts.**

- Define allocator ownership, lifetime, overflow, failure and cleanup semantics before implementing memory arenas.
- Define a stable host-call ABI and explicit capability/effect declarations.
- Keep MMIO behind a separate opt-in privileged adapter; the normal interpreter/compiler must not map physical addresses.
- Require exact device/architecture/ABI identity and independent package/signature verification in any future driver-facing service.

**Acceptance:** sanitizer-backed ownership tests, fault-injection, host-effect denial tests, ABI compatibility tests and a dedicated hardware/emulator gate. Reference-runtime tests alone do not qualify native memory or hardware behavior.

### R5 — Studio and language services

**Status: Partial-to-delivered subsets.**

- Maintain editor/LSP/DAP feature parity with the documented support matrix.
- Keep protocol handlers bounded, cancellation-aware and isolated from UI blocking.
- Expose unsupported operations explicitly instead of returning invented diagnostics or fake debugger state.
- Add Unicode/UTF-16 position tests, malformed JSON-RPC cases, cancellation tests and project-scale latency baselines.

**Acceptance:** stdio protocol tests, Windows GUI smoke test, keyboard/accessibility checks and reproducible responsiveness measurements pass.

### R6 — Jora factory and product generation

**Status: Scaffold generation delivered; application packs remain specification-only.**

- Preserve independent generated application names; the platform brand is not inserted into product names.
- Keep request, dependency graph and generated paths deterministic and validated.
- Treat generated editors/translators/audio products as non-installable scaffolds until their actual feature implementations, storage, UI, tests and package metadata exist.
- Add a separate runtime target only after a compiler/backend and conformance tests exist.

**Acceptance:** deterministic output comparison, path/symlink rejection, dependency-cycle rejection, generated-project static checks and explicit non-installable maturity metadata.

### R7 — Federation and compatibility

**Status: Metadata adapters delivered; deeper runtime integrations are Partial or Planned.**

- Pin peer interfaces to versioned manifests and explicit trust boundaries.
- Treat incoming manifests, binaries, media and reports as untrusted bounded data.
- Keep OPlague inspection read-only, VentuSample DSP offline, and Pytyliki ABI loading explicitly selected by the caller.
- Add schema compatibility, negative fixtures and cross-project contract tests for every interface change.

**Acceptance:** all federation schemas validate; version mismatch and malformed payloads fail closed; optional peers can be absent without breaking the core language runtime.

### R8 — Release and maintenance

**Status: Local package/build workflows exist; native compiler release maturity follows R3.**

- Build from a reviewed tag and exact commit.
- Record compiler/toolchain versions, source revision, artifact hashes and test evidence.
- Publish through a protected, human-reviewed release boundary.
- Preserve a rollback path to a previous known-good package.

**Acceptance:** reproducible archive inventory, verified checksums, passing required CI for the tagged commit and a maintainer-approved release.

## Not a Reaper workstream

A public hosted API, cloud deployment, kernel driver, privileged device manager and production control plane are not current Reaper product targets. They must not be marked Planned as if they were missing parts of the language unless a separately approved product decision establishes ownership and a concrete target.

## Change protocol

For each capability change, update together: owning source, regression tests, feature matrix, relevant architecture/contract page, documentation index and CI. Record the exact acceptance command and CI run. Keep Partial/Planned status when any required gate is missing.
