# DuckOS Native Target Profile for Reaper

**Version:** 0.1.0  
**Date:** 24 November 2026  
**Owner:** Reaper language and toolchain  
**Status:** target-platform specification; no claim of a complete native DuckOS backend  
**Related canonical plan:** https://github.com/Ivan-VHS/DuckOS/blob/main/docs/REAPER_DUCKOS_FULL_MIGRATION.md

## 1. Purpose

This document defines what Reaper must provide to support DuckOS as a first-class systems-programming target. DuckOS remains the owner of operating-system behavior, kernel ABI, syscalls, services, device policy and boot lifecycle. Reaper remains the owner of language semantics, compiler, runtime, standard library, target descriptions and developer tooling.

The relationship is deliberately one-way at the dependency level. Reaper must be useful as a general-purpose hosted and embedded language without DuckOS. DuckOS consumes a pinned Reaper SDK/toolchain and a versioned target profile; Reaper does not import DuckOS internals or require a DuckOS checkout to compile ordinary programs.

## 2. Verified starting point

The Reaper main branch inspected on 24 November 2026 is 9cfb9f496e3f005ca65e15df013ad7814a27f815. DuckOS main at the same review point pins Reaper commit cd84d347959f9b6cf60d87ab3d36bc94e05fd80f. Reaper main is two commits ahead of that pin. The observed delta concerns the system-capability profile, its validator/workflow and documentation indexing; it is not a reason to silently advance the DuckOS submodule.

The current language path is .rpr source → lexer/parser → Python reference runtime → CLI/Studio/LSP/DAP. The repository also contains Canonical IR, a bytecode VM, a conservative type checker, module/resource handling, an experimental scalar C17 AOT subset and a separate partial C17 frontend/IR/lowering path. The scalar AOT track emits C17 and uses a host C compiler; it is not a complete native object backend. The Python runtime remains authoritative for broad current semantics. Self-hosted lexer/parser examples cover a subset and do not establish a self-hosted compiler.

These facts determine the migration order. DuckOS kernel contracts currently written in .rpr can be checked and executed on the reference runtime, but that is not the same as native kernel execution. Reaper must not advertise freestanding readiness until the exact compiler, ABI, linker and emulator gates below are passed.

## 3. Reaper-side ownership

Reaper owns:
- language edition, grammar, canonical tokens, AST and source maps;
- localization profiles and explicit syntax-mode selection;
- name resolution, type checking, effect checking and ownership/lifetime analysis;
- HIR, MIR/CFG, canonical IR, verifier and optimizer;
- hosted reference execution, VM, native runtime and target backends;
- standard library with effect annotations and deterministic behavior;
- target descriptions, ABI lowering, object metadata and debug information;
- module/package metadata, dependency validation and linker integration;
- LSP/DAP/Studio integration for target-aware diagnostics and debugging;
- toolchain lock, compiler provenance, reproducible build and self-host bootstrap.

DuckOS owns boot protocol, kernel ABI, syscall numbering, process semantics, capabilities actually granted by the OS, VFS, device enumeration, driver loading, service manager, package policy and native user experience. A Reaper effect declaration does not grant a permission; the kernel capability broker remains authoritative.

## 4. Language edition and source compatibility

The existing source surface must remain stable through an explicit language edition. Preserve craft, make, vary, change, yield, emit, when, otherwise, each, loop while, import, export and :: flow composition for the current edition. Precedence, newline handling, block rules and import semantics must be recorded in a conformance grammar rather than inferred from implementation details.

Frontend profiles should support canonical English, Russian MOST and Ukrainian localization. Aliases normalize to the same canonical token and AST operation. Locale is declared at module or block boundary; it must not be guessed from a spelling collision. The language service uses stable diagnostic codes and localized message catalogs. Formatter preserves the module's declared dialect unless a conversion is explicitly requested.

Flow-first, classic call/expression, declarative blocks and embedded DSLs may coexist only with explicit grammar boundaries and deterministic parser selection. A file must not be parsed differently depending on the editor locale, user profile or current machine.

## 5. Type, ownership and effect system

The OS target requires a type system stronger than the current conservative inference slice. Required types include fixed-width signed/unsigned integers, usize/isize, bool, bytes/text, arrays/slices, structs, enums, tagged unions, Result/Option, opaque handles, references, pointers restricted to unsafe regions, atomics and address-space-qualified values.

Kernel and driver profiles cannot permit unknown Any values at privileged boundaries. Dynamic values in userland must be validated and converted to a typed representation before crossing into a privileged API. Every ABI-visible type needs a published size, alignment, endianness and representation.

Ownership/lifetime checking is required for pages, mappings, DMA buffers, interrupt registrations, locks, file descriptors, process handles, device sessions and IPC endpoints. The checker must prevent double release, stale resource use and invalid aliasing in the supported safe subset. Unsafe blocks are local, annotated with invariants and excluded from privileged use unless separately audited.

Effects such as file.read, file.write, process.spawn, ipc.send, net.socket, clock.read, mmio.read, mmio.write, irq.register, dma.map, memory.map, power.manage and unsafe are part of versioned language metadata. The checker propagates effects transitively across calls and imports. A package manifest declares requested capabilities, but only DuckOS can grant them to a process or module instance.

## 6. Compiler stages

The required pipeline is:

1. UTF-8 validation and source decoding.
2. Dialect-aware lexer producing canonical token IDs and exact spans.
3. Parser producing canonical AST while retaining dialect/source provenance.
4. Name and module resolution.
5. Typed HIR with explicit error/result edges.
6. Effect, capability and ownership analysis.
7. MIR/CFG with explicit control flow, drops, memory operations and atomics.
8. Canonical IR verification independent of backend.
9. Optimization passes with documented preconditions and postconditions.
10. Target lowering for the selected DuckOS profile.
11. Object emission, relocation records and debug/source metadata.
12. Linker integration with target linker script and startup objects.
13. Artifact validation and deterministic build report.

Every IR stage needs a version and verifier. An invalid intermediate representation must be rejected before code generation. Source maps survive optimization sufficiently to report source locations for compile errors, runtime faults and debugger frames.

The current stack-oriented Canonical IR and VM are useful migration foundations. They should not be silently redefined as a full systems IR. Introduce typed control-flow and resource operations through a versioned IR evolution plan, preserving old program execution and a conversion path where practical.

## 7. Native backend and object pipeline

C17 generation remains a useful transitional host backend. It does not satisfy the DuckOS kernel target by itself. The next milestones are typed scalar parity, data structures, bounded collections, explicit error handling, module interfaces, target-aware layout, debug metadata and reproducible native host compilation.

The native target pipeline must eventually produce a documented object format accepted by a pinned linker. The compiler or linker adapter must support section layout, symbols, relocations, alignment, entry symbols, debug information, stack metadata and target-specific calling conventions. A direct object writer is acceptable only after format conformance tests; a pinned external assembler/linker is acceptable as a temporary bridge if its version, arguments, inputs and outputs are verified.

The compiler must support a freestanding profile with no implicit Python runtime, hosted filesystem, environment lookup, dynamic loader or process dependency. Runtime profiles are separate: hosted CLI, native user application, freestanding boot stage, kernel module, driver module, embedded firmware and simulator. Unsupported operations fail during analysis rather than silently linking to hosted helpers.

## 8. Initial DuckOS target profile

The initial target should be one explicit x86_64 emulator-backed profile. The ADR must decide boot protocol, object format, calling convention, stack alignment, register preservation, data layout, relocation types, linker, page size, interrupt entry ABI, atomic baseline and supported CPU extensions. No second architecture is added before the first profile reaches repeatable emulator boot and ABI tests.

Future AArch64 and RISC-V64 profiles are independent machine descriptions, not branches full of target-specific conditionals in generic language semantics. Each profile defines supported instructions, atomics, endianness, stack rules, interrupt model, memory map conventions, relocation capabilities and known unsupported features.

A machine profile does not grant access to hardware. It only determines how code is generated and what target operations are legal. The OS must still initialize and authorize actual devices.

## 9. ABI and module descriptors

Reaper must distinguish generic native module ABI from DuckOS-specific driver ABI. DuckOS defines kernel ABI, syscall ABI and driver ABI. The Reaper compiler consumes those specifications and emits compatible modules.

A module descriptor should bind:
- module identity and semantic version;
- Reaper language edition and native ABI;
- compiler identity, compiler version and IR version;
- target triple/profile and object format;
- kernel ABI and driver ABI where applicable;
- exported symbol/interface hashes and required imports;
- dependency identities and versions;
- declared effects and requested capabilities;
- stack, memory and resource budgets;
- initialization, quiesce and shutdown entrypoints;
- artifact digest, signer metadata and build provenance.

The loader must reject unknown major versions, incompatible target profiles, missing imports, dependency cycles, invalid relocation, insufficient capabilities, untrusted signers and over-budget modules. A descriptor is metadata; validation alone never means the code was loaded or executed.

## 10. Standard library and host adapters

The standard library needs a deterministic core that builds without a hosted runtime: checked integer operations, memory-safe slices, byte parsing, serialization, result/error types, atomics abstraction, bounded collections, formatting and test support.

OS operations are separate capability-gated modules. File, process, network, device, time, entropy, display, audio and power providers are injected through explicit host APIs. The same pure algorithm library can be used in host tests and in DuckOS without depending on the current machine.

Kora and current host helpers should be reviewed module by module. Pure functions can become core library modules; host-specific functionality becomes an adapter; features that depend on Python or arbitrary FFI remain unavailable in freestanding profiles until replaced.

## 11. Runtime and failure semantics

Reference runtime, VM and native runtime must share language semantics for their declared feature intersection. Limits are part of the program contract: source bytes, import depth, heap, stack, call depth, execution steps, open resources, collection size, queue size and I/O payload.

The runtime defines panic/abort, cancellation, timeout, resource cleanup, error propagation and process termination. A kernel profile must not inherit Python exception behavior or host object lifetime by accident. Where unwinding is unsupported, cleanup uses explicitly generated drop paths or a documented abort policy.

Every host call validates types, sizes, ownership and capability. FFI is not an implicit bypass. Foreign functions have declared calling convention, parameter/return representation, ownership transfer, effects, thread-safety and error convention.

## 12. Debugging and developer experience

Studio/LSP should understand target profile, language edition, module ABI, type/effect/ownership errors, link errors and resource budgets. Build output includes IR and target reports, linker map, section size, stack estimates and dependency graph.

DAP needs native process attach/launch only through explicit user action and a trusted local adapter. Kernel debugging must support symbols, source maps, stack traces, register snapshots, panic context and serial/emulator logs. The UI must distinguish source-level debugging on the reference runtime from native debugging on a target binary.

Toolchain inventory may discover compilers and linkers but must not execute discovered tools merely to list them. Build invocation uses fixed argument vectors, controlled environment, bounded timeout and output limits. Tool identity is pinned or verified by digest.

## 13. Self-hosting and bootstrap

Stage 0 remains the known-good Python reference bootstrap. Stage 1 increases the set of Reaper compiler tools that can run under the Reaper VM. Stage 2 builds a native Reaper compiler for the host. Stage 3 rebuilds that compiler from Reaper source and compares normalized outputs across successive builds.

The self-hosting lexer/parser samples are milestones, not proof of full compiler self-hosting. The transition requires a published bootstrap specification, reproducible toolchain lock, deterministic compiler output, a signed recovery bootstrap and a documented emergency build path. Python is removed from the production build/runtime critical path only after native bootstrap can rebuild itself reliably.

## 14. Conformance and CI contract

Reaper owns the canonical language corpus, parser fixtures, type/effect/ownership tests, IR verifier tests, VM/native parity tests, native target ABI fixtures, object/linker tests, self-hosting checks and toolchain provenance.

DuckOS owns OS system tests, boot/driver/service tests and its application contracts. DuckOS CI checks every system .rpr file with the pinned Reaper toolchain, runs the kernel-policy contract suite on the reference runtime and VM, and adds native/emulator jobs only after the backend and target profile support them.

Required cross-project evidence includes exact submodule commit, Reaper edition, IR version, target profile, ABI versions, compiler digest, test results and generated artifact hashes. A change to public language semantics, IR, ABI or module format must trigger appropriate tests on both repositories.

The DuckOS integration must not follow mutable Reaper main. A pin update is a reviewed DuckOS change that also updates the federation registry and passes the cross-repository suite. Build pipelines do not advance pins automatically.

## 15. Acceptance gates

**Gate R0 — Language baseline.** Grammar/edition, token aliases, AST and diagnostic codes are versioned; every DuckOS Reaper module parses deterministically.

**Gate R1 — Semantic parity.** Tree-walk and VM results, output, errors, resource accounting and side effects match for the supported corpus.

**Gate R2 — Verified IR.** IR schema, verifier, CFG invariants and source maps are stable; invalid IR cannot reach a backend.

**Gate R3 — Type/effect/ownership baseline.** Privileged boundaries reject unknown types, illegal effects, invalid lifetimes and unbounded resource assumptions.

**Gate R4 — Native host parity.** A documented native subset passes differential tests against the reference runtime; debug info and deterministic build reports are available.

**Gate R5 — Freestanding object.** Reaper compiles and links a minimal freestanding program for the first DuckOS target without Python or hosted runtime dependency.

**Gate R6 — ABI conformance.** Calling convention, data layout, relocations, symbol exports, stack alignment and error return pass executable conformance tests.

**Gate R7 — Kernel integration.** A minimal Reaper-produced kernel component boots in emulator, emits structured boot evidence and survives invalid input/negative tests.

**Gate R8 — Production toolchain.** Reproducible builds, signed provenance, rollback bootstrap and target qualification are complete.

No gate inherits success from a previous gate automatically. Native host parity does not imply freestanding support; freestanding support does not imply bootability; emulator boot does not imply physical hardware qualification.

## 16. Compatibility and deprecation

Existing .rpr code remains supported according to declared edition. Breaking grammar changes require edition change and migration tooling. IR and ABI versions are separate from language edition. A language syntax feature may be available in a hosted runtime before a target backend supports it; compiler diagnostics must identify that distinction.

Deprecated runtime APIs remain available during a measured transition window. Reaper does not remove Python reference implementation merely because one native sample compiles. The Python runtime can be retired from a production package only when the documented language subset and all required OS tools have a native replacement, parity evidence, emergency recovery path and reproducible bootstrap.

## 17. Independence requirements

DuckOS may contribute system use cases and request compiler features, but Reaper's public language design remains general. The compiler must not embed DuckOS-specific policy into generic type rules. DuckOS-specific intrinsics are delivered by the selected target profile and SDK package. Other targets can supply different providers under the same language-level effect contract.

Reaper CI remains runnable without DuckOS source. DuckOS build uses a pinned Reaper release and does not depend on Reaper's working directory, developer environment or mutable branch. No source is copied between the two repositories where a versioned API or package can serve as the boundary.

## 18. Implementation checklist

- [ ] Publish a Reaper language edition and a formal grammar for the current .rpr subset.
- [ ] Add explicit locale/dialect metadata and canonical token conformance tests.
- [ ] Define typed AST/HIR and serialized IR versions.
- [ ] Add verifier coverage for all IR opcodes and control-flow invariants.
- [ ] Expand type checking and introduce target-specific layout reporting.
- [ ] Specify ownership, borrowing, resource states and deterministic cleanup.
- [ ] Introduce effect checking and capability propagation.
- [ ] Define initial x86_64 target profile through an ADR.
- [ ] Define object, relocation and linker contract.
- [ ] Implement freestanding runtime and startup profile.
- [ ] Publish DuckOS SDK compatibility metadata and module descriptor binding.
- [ ] Add native DAP/debug symbol support.
- [ ] Extend differential tests across reference, VM and native execution.
- [ ] Prove clean-room bootstrap and reproducible self-hosting.
- [ ] Update Reaper capability registry only when source and evidence exist.

## 19. Explicit non-goals

This target profile does not claim that the current compiler emits a bootable DuckOS kernel; does not make every Reaper program privileged; does not require DuckOS for hosted Reaper programs; does not treat C17 emission as full native codegen; does not turn a capability declaration into a grant; does not equate a module descriptor with a loaded driver; and does not remove all C/assembly/JavaScript/HTML/CSS where those are the narrowest platform-specific or presentation boundaries.

The target is achieved by a sequence of independently verifiable engineering gates, not by changing a project description or replacing file extensions.
