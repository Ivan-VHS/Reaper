# Reaper Systems Architecture Matrix

Reaper already maintains a 66-position systems-language matrix with project-level language capability profiles. This companion matrix adds 14 processor, microcontroller and virtual-ISA target profiles without duplicating the language catalogue.

## CLI

```sh
python -m reaper --systems-architectures
python -m reaper --architecture-profile reaper
python -m reaper --architecture-profile oplague
python -m reaper --available-architectures
python -m reaper --architectures-json
python -m reaper.systems_architectures --verify
python -m reaper.systems_architectures --profile pytyliki --tag simd,vector
```

The profile registry records data model, pointer model, byte order, execution model, ABI families, PATH-visible toolchain command candidates and capability tags. Toolchain lookup uses `shutil.which` only. A detected executable is not invoked.

## Target families

| Target | Role | Key engineering boundary |
|---|---|---|
| x86_64 / x86 | Desktop and server | SysV vs Microsoft ABI, LP64 vs LLP64/ILP32, PE/COFF decoration |
| aarch64 / armv7-m | Mobile, server and MCU | AAPCS, NEON/SVE, NVIC, memory map and interrupts |
| riscv64 / riscv32 | Modular open ISA | XLEN, extension set, privilege mode and psABI variant |
| loongarch64 | Desktop / server | LP64 ABI and platform feature discovery |
| e2k | Elbrus VLIW | MCST compiler version and VLIW scheduling boundary |
| ppc64le | Server / accelerator | ELFv2, VSX and NUMA |
| s390x | Mainframe | Big-endian data layout and vector facilities |
| avr / pic8 | 8-bit MCU | Harvard address spaces, banks, pages and memory limits |
| xmos-xcore | Deterministic multicore MCU | Hardware-thread and channel topology |
| wasm32 | Portable virtual ISA | Linear-memory bounds, WASI capability set and host ABI |

## Project profiles

- **Pytyliki:** native CPU discovery, SIMD/vector capabilities, cache/performance measurements, embedded targets and read-only host introspection.
- **Reaper:** ABI/data-layout metadata, cross-target code generation, LLVM/native targets, WebAssembly and deterministic language semantics.
- **OPlague:** Windows driver target decorations, PE/COFF, x86/Arm families, ABI boundaries and compatibility evidence.

The profiles rank relevant metadata; they do not certify target support.

## Compatibility semantics

The optional Windows INF decoration field is populated only for the known Windows architecture decoration family: `NTx86`, `NTamd64`, `NTarm`, and `NTarm64`. Other architectures have a null decoration. This is not a full INF parser and does not infer Windows support for RISC-V, E2K, WebAssembly or microcontrollers.

## Safety and truthfulness

- The matrix is descriptive reference data.
- Toolchain candidates are checked on PATH, not executed.
- No compilation, linking, emulation, firmware access, register writes or device configuration is performed.
- ABI compatibility also depends on OS, calling convention, object format, compiler flags and vendor-specific contracts.
