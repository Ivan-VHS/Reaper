# Reaper freestanding / OS toolchain

This is the first working systems-programming layer for Reaper. It adds a
cross-target native build path and a small freestanding interface without
changing the behavior of the existing Python reference interpreter.

## What is available now

- A manifest-driven **reaper os** command for native C and assembly system
  modules.
- Freestanding compilation flags: no hosted startup files, libc, compiler
  builtins, stack protector or unwind tables.
- ELF linking through Clang and LLVM lld with an explicit linker script and
  entry symbol.
- Initial target triples: **x86_64-unknown-none-elf**,
  **aarch64-unknown-none-elf** and **riscv64-unknown-none-elf**.
- **include/reaper/freestanding.h**: fixed-width compiler-native types,
  packed/aligned/section attributes, SysV64/Win64 calling-convention markers,
  volatile MMIO accessors, 32/64-bit atomics, memory fences, an acquire/release
  spin lock, a caller-owned bump arena, and x86/AArch64/RISC-V instruction helpers.
- An x86_64 COM1 example with an assembly `_start` that disables interrupts,
  installs a private 16 KiB stack, and only then calls the C kernel entry.

The header does not provide an implicit allocator or hidden runtime. The
caller owns every arena and must provide its backing memory. MMIO pointers must
refer to valid mapped device memory. Port I/O and privileged instructions are
only valid in the appropriate CPU mode and privilege level.

## Current boundaries

The **reaper os** driver compiles **C17 and assembly inputs**, not arbitrary
.rpr programs. The current .rpr interpreter is still hosted on Python, and
the native C17 language track still has a deliberately small parser/IR slice.
There is no Reaper-to-machine-code backend, general type/layout checker,
interrupt ABI lowering, DWARF emission, PE/COFF or Mach-O linker pipeline,
flat-binary writer, kernel module loader, or tested UEFI integration yet.
The target triples select Clang's code-generation target; each final binary
still needs a target-compatible linker script and startup contract.

Do not treat a successful ELF link as proof that the image boots on physical
hardware. This ELF has no Multiboot/UEFI handoff header: a loader must place it
at the linked address, enter x86_64 long mode, provide valid mappings, and
transfer control to `_start`. The entry stub then installs its own stack. The
sample uses x86 port I/O, and therefore its device output is x86-only.

## Requirements

- Python 3.10+ for the Reaper command.
- Clang with the requested target backend.
- LLVM lld (ld.lld) available on PATH.
- A linker script for the selected target.

No host C library is linked. Clang's compiler resource headers may still be
used; they are not a dependency on the target machine's libc.

## Build the sample kernel

From the repository root:

    python -m reaper os doctor
    python -m reaper os check freestanding/reaper-os.json
    python -m reaper os build freestanding/reaper-os.json --dry-run
    python -m reaper os build freestanding/reaper-os.json

The final image is written to freestanding/build/reaper-kernel.elf.

To integrate the low-level helper API into a native system module:

    #include "reaper/freestanding.h"

    typedef struct RPR_PACKED {
        rpr_u16 limit;
        rpr_u64 base;
    } descriptor_pointer;

    static volatile rpr_u32 *const device_status =
        (volatile rpr_u32 *)(rpr_uptr)0xFEC00000u;

    rpr_u32 read_device_status(void) {
        return rpr_mmio_read32(device_status);
    }

This example only demonstrates the API shape. The address is illustrative;
real device addresses must come from platform discovery and memory mapping.

The header exposes x86 port I/O, CR3/MSR access and page invalidation, plus
AArch64 barrier/TTBR0 helpers and a RISC-V I/O memory fence. It also provides
atomic loads/stores/CAS for 32- and 64-bit values. These helpers emit the
corresponding instructions; they do not check CPU privilege, device ownership,
cacheability attributes or platform-specific register availability.

## Project manifest

The manifest schema is reaper.os-project/v1. Paths are resolved relative
to the manifest. Unknown keys and unsupported output formats are rejected.
Allowed source extensions are .c, .s and preprocessed assembly .S.

    {
      "schema": "reaper.os-project/v1",
      "target": "x86_64-unknown-none-elf",
      "format": "elf",
      "entry": "_start",
      "output": "build/kernel.elf",
      "sources": ["x86_64/entry.S", "x86_64/boot.c"],
      "include_dirs": ["../include"],
      "linker_script": "linker.ld"
    }

Use reaper os targets to list configured target triples. Use
reaper os doctor to check the local compiler and linker.

## Roadmap to native .rpr kernel code

The next compiler milestones are deliberately separate from this C/assembly
bootstrap:

1. Extend the native parser from expression-only IR to typed declarations,
   functions, structs and modules.
2. Add fixed-width integer, pointer, slice, enum and explicit-layout type
   checking, including size/alignment and ABI tests.
3. Define an explicit no_std core and reject implicit allocation in
   freestanding builds.
4. Lower unsafe blocks, volatile reads/writes, atomics and constrained inline
   assembly into a target-neutral IR.
5. Add SysV64/AAPCS64/RISC-V calling-convention lowering and interrupt entry
   stubs.
6. Emit relocatable objects and linkable ELF images, then add debug info and
   additional object formats.
7. Build and boot conformance kernels under emulators before declaring
   hardware-facing features stable.

Until these gates pass, system code that needs machine instructions belongs
in the native C/assembly bridge while .rpr remains the orchestration and
description language.
