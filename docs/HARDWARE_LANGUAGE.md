# Reaper as a systems and hardware language

**Author and project maintainer:** Ivan-VHS  
**Status:** Reaper-native Typed Registry v1 and first checked MMIO adapter contract; first-class aggregate grammar and native lowering remain separate milestones  
**Scope:** language, compiler, runtime, embedded targets and Reaper Studio

Reaper is being repositioned from a flow-first general-purpose language toward a systems language for firmware, embedded software, platform services and hardware-adjacent development. The existing .rpr surface and Python runtime remain part of the compatibility product while a native compiler path grows toward the canonical execution route.

This document separates what is already in the repository from the target design. The executable Reaper .rpr Typed Registry is implemented in the reference runtime; it is not yet first-class compiler syntax or native aggregate lowering. See [Typed Registry v1](TYPED_REGISTRY.md).

## Product contract

Reaper should make low-level work inspectable and explicit:

- target architecture, ABI, memory map and linker layout are named in the build profile;
- ownership, mutability, lifetimes, effects and hardware capabilities are visible;
- memory accesses have explicit width, alignment, byte order and ordering semantics;
- dangerous operations require an explicit capability and an OS/platform adapter;
- generated IR, assembly, object metadata, stack use and linker maps are inspectable;
- the same source can be checked on a host, simulated, cross-compiled and then qualified on hardware;
- compatibility is maintained through versioned language, ABI and target contracts.

The language is not allowed to imply that user-space code can safely access arbitrary physical addresses, install drivers, flash a board or enter kernel privilege on its own.

## What exists today

| Area | Evidence-backed repository state | Boundary |
|---|---|---|
| Reaper source language | .rpr lexer, parser and Python reference runtime | Python remains the broad compatibility implementation |
| Native compiler | scalar AOT subset emits C17 and invokes a host GCC/Clang-compatible compiler | no full native parity, no direct ELF/PE/Mach-O emitter |
| C17 core | native lexer, expression parser, owned AST, checked integer IR, constant folding and limited lowering | IR and parser cover only a small subset |
| QCS | separate hardware-domain lexer/parser and JSON AST | design/validation frontend, not device execution |
| Embedded workbench | MCU profiles, Flash/SRAM maps, linker-script generation and cross-compiler process invocation | no board flashing or physical MMIO |
| Studio | Windows editor/debugger foundation plus a Systems/Hardware overview showing MCU profiles and current access limits | no live device inspector or complete hardware IDE |
| Native capability catalogue | versioned module and operation descriptions with a small set of C primitives | catalogue entries are not automatically executable handlers |
| Typed Registry | Reaper .rpr constructors, target-aware layouts, platform/ABI checks and binding/effect/capability validation | parser-level aggregate declarations, HIR/MIR lowering and native object emission are not implemented by this registry |

## Target language layers

1. **Core syntax and semantics.** Keep craft, make, vary, change, yield, emit and :: source compatibility. Add system constructs only through a versioned grammar and semantic contract.
2. **Type and effect system.** Fixed-width integers (u8 through u128, i8 through i128), usize/isize, pointer and reference types, arrays/slices, structs, enums, tagged unions, function pointers, atomics, explicit result/error types, address-space qualifiers and physical units. Hardware and OS effects are part of function signatures.
3. **Ownership and resource lifecycle.** Immutable bindings by default; affine/linear ownership for DMA buffers, mappings, locks, interrupts, handles and device sessions; deterministic defer/drop semantics; borrow checking that prevents overlapping mutable aliases and use-after-release.
4. **Memory model.** Stack, static, heap, region/arena and device memory are distinct. volatile is not treated as a substitute for atomics or memory barriers. Alignment, aliasing, initialization, endianness, packed layout and lifetime rules are checked explicitly.
5. **Hardware surface.** Typed MMIO register blocks, bitfields, port I/O where supported, interrupt declarations, DMA buffer lifecycle, bus transactions, timers, watchdogs, cache maintenance, atomics and architecture-specific intrinsics. Every operation is capability-gated and target-checked.
6. **Effects and privilege.** Separate pure code from io, mmio, irq, dma, clock, process, network and unsafe effects. A program requests capabilities in its manifest; the host kernel/driver decides whether to grant them.
7. **Native compiler.** Canonical versioned IR with source maps; HIR for typed operations; MIR/CFG for control flow, ownership, drops and effects; target lowering; optimization passes with verified invariants; backend to host C17 during migration, then a native code/object backend; linker and firmware image metadata.
8. **Runtime profiles.** Hosted, freestanding, no_std, boot-stage, kernel-driver, MCU and simulator profiles have distinct startup, panic, allocator, threading and I/O contracts.

## Implemented Reaper Typed Registry

The shared [Typed Registry v1](TYPED_REGISTRY.md) is executable Reaper source in `stdlib/typed_registry.rpr`. It declares fixed-width scalar, pointer, array, struct and enum descriptors; calculates target-dependent layouts; validates platform/ABI tuples; and checks binding types, effects and requested capabilities. `examples/typed_registry.rpr` is the executable conformance fixture and CI runs it.

This API intentionally uses the current Reaper grammar. It does not claim dedicated `struct`/`enum` syntax, compile-time type resolution or native backend support.

## Proposed source surface

The following illustrates where the language is heading. It is not claimed to compile with the current parser or runtime.

~~~reaper
device gpio0 : MmioRegion<0x48000000, 0x400>
    register mode   : u32 at 0x00 read_write
    register input  : u32 at 0x10 read_only
    register output : u32 at 0x14 write_one_to_set

craft set_pin(pin: u5, enabled: bool) -> Result<(), DeviceError>
    effect mmio.write
{
    let mask: u32 = 1u32 << pin
    if enabled {
        gpio0.output.write_one(mask)?
    } else {
        gpio0.output.clear(mask)?
    }
    yield Ok(())
}
~~~

The compiler must reject a register whose address, width, access policy or target mapping is invalid. The driver or platform adapter owns the actual mapping and performs the transaction.

## Current native MMIO foundation

The C API in include/reaper/hardware.h provides:

- MMIO region and register descriptor validation;
- 8/16/32/64-bit width checks, bounds and natural-alignment checks;
- read-only, write-only, read-write, write-one-to-clear and write-one-to-set access policies;
- explicit endian and memory-order metadata;
- capability checks before read/write callbacks;
- a host-supplied bus adapter, enabling deterministic fake-device tests.

The API does **not** map physical memory, execute privileged instructions, register real interrupts, allocate DMA memory or communicate with a real device by itself. A trusted OS driver/HAL must supply the adapter and enforce platform-specific mapping, cache, barrier and privilege rules. W1C/W1S writes are passed as explicit values; clients must not implement them as an implicit read-modify-write sequence.

## Reaper Studio: hardware workbench direction

The Studio roadmap is centered on a target workspace, not decorative widgets:

- target selector and immutable build profile (triple, ABI, CPU features, memory regions and linker script);
- project and source explorer with device/board manifests;
- compiler diagnostics linked to source, types, capabilities and target constraints;
- HIR/MIR/CFG and ownership/effect visualizers;
- register-map editor with address, width, reset value, access policy and bitfield inspection;
- memory-map view for Flash, SRAM, ROM, MMIO and reserved regions;
- generated C/assembly/object inspector and linker-map report;
- stack/heap/section budget checks and reproducible build fingerprints;
- QEMU or vendor simulator launch profiles, with hardware flashing disabled until an explicit reviewed adapter exists;
- debugger panels for registers, breakpoints, memory regions and interrupt traces when the selected target/debug probe supports them;
- permission prompts for hardware access and a persistent audit trail of privileged actions.

The UI must label every feature as available, experimental, adapter-dependent or planned. A generic simulator is not evidence of physical-board support.

## Migration and acceptance gates

### Gate A — contract foundation

- Keep the Python runtime and current .rpr behavior as compatibility oracle.
- Version the native IR and add typed integer, pointer, aggregate, load/store and call contracts.
- Expand the native parser from expression-only to declarations, blocks and functions.
- Add the checked MMIO descriptor API and fake-bus tests.
- Add differential fixtures so a native implementation must match the Python semantics where both support a construct.

### Gate B — systems semantics

- Implement static types, target-aware layouts, ownership/borrowing, deterministic drops and effect checking.
- Define ABI rules for C interop, calling conventions, struct layout, symbol visibility and unwind/panic behavior.
- Add explicit unsafe boundaries and audited capabilities; no default raw-pointer or physical-memory access.

### Gate C — real native backend

- Compile a useful subset to target objects and executables for x86_64 and AArch64, then selected MCU targets.
- Add target triples, compiler/linker discovery, toolchain pinning, linker-script validation and reproducible builds.
- Verify code generation with unit tests, differential execution, fuzzing, disassembly inspection and benchmark baselines.
- Do not call the language self-hosting until its compiler is built and tested from Reaper source.

### Gate D — hardware qualification

- Implement OS/driver-backed MMIO mappings, interrupt service registration and DMA allocation/synchronization per platform.
- Validate with emulators, hardware-in-the-loop tests and physical boards from an explicit support matrix.
- Require driver signing, privilege separation, rollback and vendor/architecture verification for any driver installation workflow.
- Keep device support read-only by default until an explicit user action authorizes a mutation.

### Gate E — Studio and distribution

- Align CLI, LSP, DAP, build engine and Studio on one versioned compiler service.
- Package Windows, Linux and macOS Studio builds when their native UI and debugger paths pass CI.
- Publish target support, maturity, benchmark methodology, security boundaries and reproducible release artifacts.

## Positioning and message

**Primary line:** Reaper — the systems language and hardware workbench.

**Supporting message:** Write close to the machine. Keep memory, effects and device access explicit. Inspect every compiler stage. Build for the host, firmware and platform targets through a verifiable toolchain.

**Who it serves:** embedded and firmware developers, systems programmers, driver/platform engineers, compiler researchers and educators.

**What can be claimed now:** an experimental native AOT scalar compiler, a C17 front-end/IR slice, QCS hardware parser, MCU profile/linker tooling and a Windows Studio foundation.

**What cannot be claimed yet:** a complete Rust/C++-class systems language, a self-hosted compiler, direct machine-code backend, general-purpose hardware execution, production MMIO/IRQ/DMA runtime, signed driver suite or complete hardware IDE.

## Release policy

Use three separate labels:

- **Available:** implemented, tested and callable through a stable interface.
- **Experimental:** implemented with limited scope or host-specific constraints.
- **Planned:** a design or roadmap entry without executable support.

A capability enters marketing copy as available only after its contract, implementation, tests and supported-target evidence are published together.


## DuckOS system-service boundary

The downstream DuckOS integration is specified separately in [DUCKOS_SYSTEM_SERVICE_CONTRACTS.md](DUCKOS_SYSTEM_SERVICE_CONTRACTS.md), with a machine-readable registry at [language/duckos_system_services.v1.json](../language/duckos_system_services.v1.json). These are host-call contracts only: they do not add callable functions to the current Reaper runtime. DuckOS owns the kernel, HAL, driver and service implementations; Reaper owns versioned types, effects, capabilities and ABI validation. Keep user-mode orchestration separate from privileged kernel adapters, and keep Linux-specific mechanisms behind optional target backends.
