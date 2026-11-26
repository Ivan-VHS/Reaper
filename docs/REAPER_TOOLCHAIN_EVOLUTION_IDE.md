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

## Review-gated patch proposals

`tools/reaper_patch.py` writes proposal schema `reaper.patch-proposal/v2`.
Patch bytes and Git blob bytes are kept unchanged end-to-end, so SHA-256
checks preserve CRLF and binary content. Git parses the patch file list;
every parsed path must have exactly one manifest entry with an explicit
base-file presence flag and base-content digest. Invalid patch sections,
incomplete manifests, path traversal and symlink components fail closed.

Proposals created with schema v1 must be regenerated with the current tool:
v1 did not record base-file presence and could hash CRLF content after text
normalization. Applying and rollback remain explicit reviewer actions; the
tool does not execute proposal commands or merge branches.
