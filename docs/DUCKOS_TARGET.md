# DuckOS freestanding kernel target profile

## Purpose and maturity

This profile makes the DuckOS compiler requirements explicit in Reaper's own repository. It is a **planned target contract**, not a supported cross-compilation target. The machine-readable profile is language/targets/duckos-kernel.v1.json and is validated against schemas/system-target.v1.schema.json.

DuckOS currently runs its .rpr system-policy contracts on Reaper's hosted reference runtime and VM. Reaper's experimental native AOT backend emits C17 for a restricted scalar subset and invokes a host GCC/Clang-compatible compiler. It does not emit target objects directly, does not provide freestanding startup and does not compile the lists, indexing, each, imports and collection pipelines used by DuckOS contracts. Therefore no current DuckOS .rpr file is proven to compile into a freestanding kernel object.

## Target decisions

The initial CPU architecture, target triple, boot protocol, kernel ABI, endianness, pointer width, memory map, interrupt controller and timer source remain unset until DuckOS records approved architecture decisions. Compiler support must not freeze these values by guessing them from package metadata or examples.

A versioned boot handoff and the existing C MMIO descriptor/bus adapter are useful boundaries, but neither is a bootloader or physical-device implementation.

## Compiler capability gates

| Gate | Required result |
|---|---|
| Language surface | native lowering of the actual DuckOS source constructs, with reference-runtime differential fixtures |
| Types and layout | fixed-width integer/pointer types, target-size aliases, aggregate ABI, field offsets and alignment |
| Runtime profile | no host standard library, explicit entry, panic path, allocator contract and deterministic initialization |
| Safety model | ownership, borrow/lifetime, initialization, deterministic drop and explicit unsafe/effect/capability checks |
| Hardware semantics | typed volatile MMIO, atomics, fences, DMA lifecycle, interrupt ABI and reviewed assembly boundary |
| Object/linker | target objects, relocations, sections, linker script, symbol visibility and unresolved-symbol audit |
| Debugging | source maps, DWARF or target metadata, panic traces and emulator symbolication |
| Qualification | pinned cross-toolchain, reproducible image, host differential tests and QEMU boot regressions |

No registry item alone counts as implementation. A capability is available only after source semantics, runtime/compiler path, tests and supported-target evidence agree.

## Migration boundary

Keep the Reaper Python reference runtime as the language-semantics oracle during the migration. The existing stack VM IR remains an execution format for the hosted VM; semantic analysis and eventual native lowering must have versioned source maps and verifiable contracts. Expand the native subset in measured, testable stages. Do not create a separate DuckOS-only language fork.

Architecture-specific bootstrap assembly may remain as a small reviewed boundary where the processor requires instructions unavailable to the language backend. It must use a versioned ABI and be covered by target tests. DuckOS host-side build tools and the Mora browser shell are not kernel code; they need an explicit product boundary rather than being silently included in the kernel migration percentage.

## Promotion criteria

A kernel milestone may be promoted from planned only after a real Reaper-generated target object exists, its sections/relocations/undefined symbols are inspected, the approved linker produces a reproducible image, and the image boots in the selected QEMU machine profile with a serial marker. Reference runtime execution and VM tests are necessary but insufficient evidence.

See the DuckOS migration roadmap for the 19-source baseline, G0–G7 phase gates and the cross-repository CI loop.
