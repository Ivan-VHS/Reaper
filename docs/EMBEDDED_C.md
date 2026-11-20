# Embedded C in Reaper

Reaper's reference runtime now includes a target catalogue, PATH-only compiler
discovery, bounded source inspection and deterministic argv-style build plans.
It does not silently spawn a compiler, load native code, execute firmware,
write peripheral registers or flash a device.

## Language functions

\`\`\`reaper
make profiles := embedded_targets()
make arm := embedded_profile("arm-cortex-m0")
make compiler := embedded_toolchain("arm-cortex-m0")
make review := embedded_inspect("#include <stdint.h>\nvoid task(void) {}")
make plan := embedded_build_plan("arm-cortex-m0", "src/main.c", "build/main.elf")
emit arm["compiler"]
emit compiler["available"]
emit plan["command"]
\`\`\`

- \`embedded_targets()\` returns all seven reference profiles.
- \`embedded_profile(name)\` returns one profile or reports an unknown name.
- \`embedded_toolchain(name)\` checks candidate executable names with
  \`shutil.which\`; it does not launch the compiler.
- \`embedded_inspect(source)\` scans at most 1 MiB and reports include lines,
  likely dynamic-allocation calls, blocking delays, register-oriented markers
  and host-I/O calls. Comments and string literals can affect heuristic counts.
- \`embedded_build_plan(target, source, output)\` returns an argv list. It never
  executes that list; inspect and run it explicitly with a trusted toolchain.

The target profiles are AVR ATmega328P, ARM Cortex-M0, RISC-V32 IMAC, MSP430G2553,
Xtensa ESP32, WebAssembly/WASI and host C11. The ESP32 profile does not replace
ESP-IDF project configuration. MCU-specific clocks, peripheral maps, linker
scripts, startup code, pin assignments and real-time guarantees are intentionally
not guessed.

## Pytyliki native ABI

When native FFI is explicitly enabled, Reaper can query the additive Pytyliki
ABI v1 functions through the explicit absolute path to the Pytyliki FFI library:

\`\`\`reaper
make targets := pytyliki_embedded_targets("/absolute/path/to/libpytyliki_ffi.so")
make review := pytyliki_embedded_inspect("#include <stdint.h>", "/absolute/path/to/libpytyliki_ffi.so")
\`\`\`

Run with \`--allow-native-ffi\`. Native library loading executes trusted native
code in-process and is not a sandbox. The adapter validates ABI v1 and requires
the additive Embedded C symbols; older libraries continue to support the
pre-existing metric API but do not expose the new Embedded C methods.

## CLI

\`\`\`sh
reaper --embedded-targets
\`\`\`

The CLI prints serializable target metadata as JSON. No firmware execution,
programming, flashing or covert function injection is provided.
