# Embedded C workbench

Reaper supplies a compact Embedded C project workflow in its Python runtime and
Reaper Studio. Pytyliki provides the native C11 profile, register and budget
primitives used alongside it.

## Scope and trust boundary

The built-in Cortex-M4 and RV32IMC profiles are **reference configurations**,
not guaranteed board definitions. Their memory sizes and addresses must be
replaced with values from the exact MCU datasheet or a vendor SVD. The AVR
profile identifies ATmega328P, but its board clock and fuse configuration still
need verification.

The starter image links a freestanding C entry point at \`main\`. It deliberately
does not invent a reset vector, startup sequence, clock tree, pin mux, boot
protocol or SWD/JTAG transport. Add the vendor startup code and board-specific
initialization before treating an ELF/BIN/HEX file as flash-ready. No command in
this workbench flashes a device or writes host MMIO.

## CLI

~~~sh
python -m reaper embedded profiles
python -m reaper embedded profile cortex-m4-reference
python -m reaper embedded init ./board --profile cortex-m4-reference
python -m reaper embedded inspect ./board
python -m reaper embedded build ./board
~~~

Project files:

- \`embedded.json\`: target metadata, compiler, flags, source list, memory map and
  reserved stack budget.
- \`linker.ld\`: generated GNU linker script.
- \`src/main.c\`: small freestanding C11 starter.
- \`build/firmware.elf\` and \`build/firmware.map\`: linker outputs. When matching
  GNU \`objcopy\` is installed, the builder also emits \`.bin\` and \`.hex\`.

The builder discovers compilers with \`PATH\` lookup, passes an argv array rather
than a shell command, and applies a timeout. It does not install dependencies.
Source and linker-script paths must remain inside the project directory.
Treat source files, compiler binaries, compiler plugins and toolchain configuration
as trusted: a compiler is native executable code, not a sandbox.

## Memory accounting

FLASH usage = \`.text + .isr_vector + .rodata + .data\`.

SRAM usage = \`.data + .bss + .noinit + configured stack reserve\`.

The section parser uses GNU \`size -A\` when available and falls back to a GNU
linker map parser. The estimate is not a stack high-water measurement; runtime
stack, heap, DMA and vendor-reserved regions need additional project-specific
budgeting. A result over either configured region is returned as an explicit
warning and a non-zero CLI exit code.

## Register and telemetry model

\`RegisterBank\` is an in-memory simulator only. It never dereferences physical
addresses. It can enforce read-only registers and writable masks. \`load_svd\`
imports a common CMSIS-SVD peripheral/register subset (base address, offset,
reset value and access).

The incremental telemetry frame format is:

~~~text
A5 | command:u8 | payload_length:u16_le | payload | crc8:u8
~~~

CRC-8 uses polynomial \`0x07\`, initial value zero. The decoder accepts partial
chunks, discards malformed frames and resynchronizes at the next \`0xA5\` marker.
This is a project-local framing primitive, not a standard MCU boot protocol.

## Studio

The **Embedded C** menu creates a starter project, inspects its profile and runs
the bounded cross-build in a worker thread so the editor remains responsive.
Compiler diagnostics are appended to the Studio output pane. The register and
telemetry classes are available to Python integrations and tests; this first
iteration does not claim an on-chip debugger, live pin sampling, UART upload or
JTAG/SWD support.

## Verification

~~~sh
python -m unittest discover -s tests -p 'test_embedded.py' -v
~~~

The tests cover profile validation, linker generation, project creation,
memory accounting, GCC diagnostic parsing, GNU map/size parsing, SVD metadata,
simulated register permissions and incremental telemetry framing.
