# Native ELF64 relocatable object writer

The native C17 track includes a writer for deterministic, little-endian x86-64 relocatable objects (ET_REL). The writer serializes ELF64 structures itself and does not invoke GNU as, LLVM MC or another host assembler.

## Input model

The caller supplies zero-based arrays of sections, symbols and relocations. Sections support SHT_PROGBITS and SHT_NOBITS. Symbols support local, global and weak binding. Undefined and absolute section sentinels are separate from zero-based user section indices.

The output contains a null symbol, local section symbols, user symbols ordered local-before-global, .symtab, .strtab, .shstrtab and one SHT_RELA section for each user section that has relocations.

## Supported x86-64 relocations

| Relocation | Type | Field width |
|---|---:|---:|
| R_X86_64_64 | 1 | 8 bytes |
| R_X86_64_PC32 | 2 | 4 bytes |
| R_X86_64_PLT32 | 4 | 4 bytes |
| R_X86_64_32 | 10 | 4 bytes |
| R_X86_64_32S | 11 | 4 bytes |

The writer validates section types and alignment, symbol section/value bounds, relocation target ranges and symbol indexes, supported relocation types, and the non-extended ELF section-count limit. The returned buffer is caller-owned and released with reaper_elf64_buffer_destroy.

## Build and test

Configure the native C17 project with REAPER_BUILD_TESTS=ON, build it with CMake and run CTest. The dedicated native-elf64-writer test checks ELF identification/header fields, section/string-table layout, symbol-table ordering, relocation links and addends, NOBITS handling, malformed input and empty object output.

## Current boundary

This is an ELF relocatable-object writer, not a complete toolchain. It does not yet resolve symbols, extract archives, merge sections, apply relocations, construct GOT/PLT, produce ET_EXEC or ET_DYN images, build program headers, dynamically link, or load a process. It is not yet connected to Reaper's machine-code emitter. The existing host-assembler object path remains available until native code generation feeds this object model.

Ivan-VHS is the project author/developer. Retain original copyright and notices for any third-party code or format-specific implementation later integrated.