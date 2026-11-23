# Native ELF64 writer and static linker

Reaper's ELF64 track contains a deterministic ET_REL writer and a bounded static x86-64 linker.

The linker merges .text, .rodata, .data and .bss, resolves local/global/weak symbols, applies R_X86_64_64, PC32, PLT32, 32 and 32S relocations, and emits a loadable ET_EXEC image with four PT_LOAD headers. Its entry point must resolve to a symbol inside .text.

This first target is static Linux x86-64. It does not implement PT_INTERP, dynamic libraries, archive extraction, GOT synthesis, TLS, unwind metadata, C runtime startup or PIE/ASLR. It expects a self-contained entry routine such as _start.

The static linker consumes the in-memory ET_REL object model. Reaper's scalar AOT compiler still emits C17 and calls the host compiler, so direct source-to-ELF lowering is not yet connected.
