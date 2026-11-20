# Low-level interoperability and copyright inventory

## Scope

The Reaper 0.1 repository adds an original metadata catalogue for the exact 40 ecosystems requested:

| Group | Entries |
|---|---:|
| Processor ISAs: x86, ARM, RISC-V, MIPS, AVR, 6502, Z80 | 7 |
| Systems languages: C, C++, Rust, Zig, D, Nim, Ada, Modula-2, Oberon | 9 |
| HDL and hardware construction: Verilog, SystemVerilog, VHDL, Chisel, Bluespec | 5 |
| Bytecode / VM / IR: WebAssembly, LLVM IR, JVM, Dalvik, LuaJIT, Forth, PostScript, BCPL, BLISS | 9 |
| Specialized: Brainfuck, FALSE, Befunge, Malbolge, Piet, Whitespace, GLSL, HLSL, SPIR-V, PTX | 10 |
| **Total** | **40** |

The catalogue is maintained in reaper/interop_matrix.json and validated by reaper.interop. Every record identifies the ecosystem family, a short original description and optional external command candidates.

## Commands

~~~sh
# Validate the complete 40-entry catalogue
reaper interop verify

# List every ecosystem
reaper interop list

# Filter a category or emit machine-readable data
reaper interop list --group isa
reaper interop list --group hdl --json

# Show only tool command names currently discoverable on PATH
reaper interop list --available-only
reaper interop list --group systems-language --available-only
~~~

The probe calls the platform's executable lookup (shutil.which) only. It does not run an external compiler, load a binary, execute user code, install packages, compile, link, emulate an ISA or access hardware. A command found on PATH is not proof that it supports a specific target, ABI, language version or feature.

**Implementation status:** this feature is interoperability metadata and toolchain discovery. It does not claim a native backend, parser, assembler, simulator or VM implementation for every catalogue entry. Existing Reaper functionality such as the Python interpreter, Canonical IR/VM, C ABI bridge, embedded project scaffolding and architecture matrix remains separately documented and tested.

## Copyright and attribution inventory

Reaper is distributed under Apache License 2.0. New first-party code in this feature is original implementation code; the catalogue contains names, command candidates and concise factual descriptions rather than copied compiler, architecture-manual, HDL or VM source.

Run an inventory against a project:

~~~sh
reaper copyright-scan .
reaper copyright-scan ./path/to/project --json

# CI gate: every discovered source file must carry a file-level SPDX identifier
reaper copyright-scan . --require-spdx
~~~

The scanner:

- inspects a bounded set of source files and the first 80 lines (up to 16 KiB) for SPDX-License-Identifier and copyright markers;
- inventories root-level LICENSE, COPYING and NOTICE files;
- reports files with an explicit SPDX identifier, files in a repository that has a root license file, and files requiring license review;
- skips common generated/cache directories and symbolic links, and has file-count and byte limits;
- can return JSON for CI and compliance review.

The repository-license-present classification means only that a root-level license file exists. It does not infer that the root license legally covers every file. The --require-spdx flag checks for a file-level identifier even when a root license file exists.

## Legal and technical limits

This tool is a compliance inventory, not legal advice. It does **not**:

- detect plagiarism or compare source code against private or public repositories;
- establish authorship, provenance, ownership, permission or copyright status;
- validate an SPDX identifier against the complete SPDX License List or resolve an SPDX expression;
- determine whether two licenses are compatible or whether a use is permitted;
- scan every binary, generated artifact, package lockfile, submodule, vendored dependency or external toolchain;
- prevent a user from copying, publishing or executing code.

Before importing third-party code or redistributing binaries, maintain the original license text, copyright notices, NOTICE obligations and source attribution required by the applicable license. Review each dependency and generated artifact independently. Do not remove upstream notices. Use an approved legal review for ambiguous or mixed-license material.

The names of instruction sets, languages, virtual machines and file formats are recorded as ecosystem identifiers. The implementation intentionally does not copy protected source code, vendor proprietary compilers, or reproduce third-party documentation.
