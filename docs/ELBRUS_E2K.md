# Elbrus E2K support

## Support model

Reaper has two distinct execution tracks; both must be assessed independently on E2K:

| Layer | E2K support boundary |
|---|---|
| Python reference runtime | Runs when the target OS provides Python 3.10+ and the required standard-library modules |
| C17 native runtime | Uses the portable CMake target and can be built with MCST LCC; verify CTest on native E2K |
| Language service / CLI / parser | Architecture-neutral Python implementation |
| Explicit Pytyliki C ABI bridge | Supported only when the explicitly selected shared library was built for the same E2K OS/ABI |
| Node.js / V8 integration | Depends on an official E2K-compatible Node.js distribution; not implied by the Python or C17 build |
| Windows Studio | Windows-specific packaging; not included in the E2K Linux core build |

The systems architecture catalogue already contains the `e2k` / Elbrus profile. It is a target
description and toolchain lookup hint, not a claim that a compiler is installed or that generated
binaries were executed.

## Toolchain

Use the MCST System Programming Kit (SDK) and its LCC-compatible C compiler driver. MCST documents
native `gcc` / `g++` aliases for LCC and a separate licensed cross-compiler route. The MCST SDK
matrix currently lists LCC 1.31, binutils 2.45 and GDB 17.1 for the newest Elbrus Linux 10 line;
match the package to the exact processor generation and OS release.

- [MCST SDK](https://www.mcst.ru/SDK)
- [LCC compiler and language support matrix](https://www.mcst.ru/LCC)
- [MCST download portal](https://dev.mcst.ru/download/)
- [E2K compiler programming guide](https://dev.mcst.ru/book/chapter1.html)

## Native build and tests

On a native Elbrus Linux host:

```sh
CC=gcc CXX=g++ bash scripts/elbrus/build-e2k.sh
```

The script verifies the `__e2k__` compiler macro, builds the C17 target, runs CTest, and then
runs the Python reference tests and example validation. Python checks are skipped only when
Python 3.10+ is unavailable; the C17 build is not silently substituted for the Python runtime.

## Cross compilation

A reusable Linux/E2K toolchain file is available at
`cmake/toolchains/elbrus-e2k.cmake`:

```sh
E2K_CC=/opt/mcst/bin/e2k-gcc E2K_SYSROOT=/opt/mcst/sysroot \
  cmake -S . -B build-e2k-cross \
  -DCMAKE_TOOLCHAIN_FILE=cmake/toolchains/elbrus-e2k.cmake \
  -DREAPER_BUILD_TESTS=ON
cmake --build build-e2k-cross --parallel
```

Use the compiler and sysroot delivered with the matching MCST cross-toolchain package; the path
above is illustrative. A cross build does not execute the produced program. Run the native tests
on E2K, or configure a separately validated `qemu-e2k` emulator.

## Compatibility and optimization rules

- Keep the portable C17 implementation as the baseline; use `__e2k__` only for measured,
  documented target-specific implementations.
- Do not assume LLVM/Clang emits valid E2K machine code merely because the tools are installed.
- Do not infer support for arbitrary C++ standards from LCC's C/C++ driver. This repository's
  native C track is C17.
- Shared libraries are trusted native code. Continue to require an explicit absolute path and
  ABI-version check in the Pytyliki bridge.
- Treat LCC optimization decisions and performance counters as target-specific; record compiler,
  CPU generation, OS, flags and repeated measurements.

## CI

`.github/workflows/elbrus-e2k.yml` can run on a configured self-hosted runner labelled
`self-hosted, linux, e2k`. Dispatch it with `run_on_e2k_runner=true`; hosted x86 test coverage
continues to run separately.
