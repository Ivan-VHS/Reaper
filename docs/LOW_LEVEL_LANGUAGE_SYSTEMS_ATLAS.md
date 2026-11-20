# Low-Level Language and Systems Architecture Atlas

Reaper now carries a searchable, immutable research atlas for 66 low-level and systems languages and 14 architecture targets. It is an engineering reference and a design-space exploration aid, not a toolchain manager or a claim that Reaper implements the listed languages.

## CLI

```sh
python -m reaper --atlas
python -m reaper --atlas --atlas-kind languages
python -m reaper --atlas --atlas-kind architectures
python -m reaper --atlas --atlas-query Vale
python -m reaper --atlas --atlas-kind languages --atlas-query linear
```

The Python API is available through `reaper.atlas`:

- `LANGUAGES`: 66 profiles with memory, compilation, assurance and design-signal fields.
- `ARCHITECTURES`: target profiles for x86, Arm, RISC-V, LoongArch, E2K, Power, IBM Z, microcontrollers, XMOS and WebAssembly.
- `search_atlas(query, kind)`: deterministic search across the descriptive fields.
- `format_atlas(kind, query)`: stable terminal and CI output.
- `validate_atlas()`: checks count, IDs, uniqueness and required fields.

## How profiles relate to Reaper

| Atlas idea | Reaper engineering translation |
|---|---|
| Linear / unique ownership | Future static resource-flow analysis; runtime semantics remain unchanged until tests exist |
| Compile-time execution and reflection | Constant-folding and compile-time evaluation behind explicit evaluation budgets |
| Typed intermediate representations | Preserve source locations, type facts and effect metadata through canonical IR |
| Contracts and dependent types | Add preconditions, postconditions and proof obligations as diagnostics, not silent assumptions |
| CSP and actor systems | Model channels and message passing as explicit effects before exposing concurrency |
| GPU / DSP / accelerator targets | Introduce capability-checked backends with deterministic fallback behaviour |
| ABI and data layout | Make target triple, pointer width, alignment and calling convention explicit in any native backend |

## Architecture profiles

The architecture index includes x86_64, x86, AArch64, ARMv7-M, RISC-V 32/64, LoongArch64, E2K, PowerPC64LE, s390x, AVR, PIC8, XMOS xCORE and WebAssembly32. They are described independently of the host running the Python interpreter.

## Safety and truthfulness

- The atlas never invokes a compiler, linker, assembler, emulator or package manager.
- A listed compiler backend is descriptive metadata, not proof it is installed or supported by the current build.
- Historical and research languages remain labelled as such; no compatibility is inferred from syntax similarity.
- Reaper's existing interpreter remains the semantic reference. New ownership, effect or native-code features require their own design, conformance tests and resource budgets.
