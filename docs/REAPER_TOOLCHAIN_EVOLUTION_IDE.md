# Toolchain and IDE

| Tool | Current role |
|---|---|
| CLI | run/check/REPL/module graph |
| Studio | Windows edit/check/run/debug |
| VS Code | syntax/editor integration |
| Python | reference runtime |
| CMake/C17 | native build/test track |

An editor integration does not imply compiler, debugger or native runtime parity.


## Systems and hardware direction

The product direction is now a systems-language toolchain: target triples and ABI profiles, typed memory layouts, ownership/effect analysis, QCS-to-language convergence, native object generation, embedded linker reports and device adapters. The current MMIO C API is a checked descriptor/capability layer only; it does not map physical memory or replace a driver. Reaper Studio hardware views (target selector, register map, memory map, IR/assembly inspector, budgets, simulator and debug-probe adapters) remain roadmap items. See [HARDWARE_LANGUAGE.md](HARDWARE_LANGUAGE.md) for acceptance gates and maturity labels.