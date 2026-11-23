# Native Reaper → DABI64 → ELF64 pipeline

Status: executable native-runtime pipeline foundation. It does not yet replace the Python reference runtime or produce a standalone compiler executable from arbitrary `.rpr` source.

## Compiler integration

```
Reaper canonical integer IR
  -> reaper_dabi_lower_ir
  -> verified ReaperDabiProgram
  -> DABI64 runtime-call table
  -> owned execution frame
```

The canonical IR lowering currently supports `CONST_I64`, `ADD_I64`, `SUB_I64`, `MUL_I64`, `DIV_I64`, and `RETURN`. Unsupported canonical IR opcodes fail closed.

The DABI64 program IR adds text constants, checked integer operations, calls, conditional/unconditional branches and return. Runtime calls use the stable call table for string construction/concatenation/length, array create/push/get/length, iterator begin/next and `emit`. This lets the native program representation express:

```
items = ["red", "blue"]
iter = iterator.begin(items)
loop:
    has_item, item = iterator.next(iter)
    if not has_item: return
    emit(item)
    jump loop
```

This is the lowered instruction pattern, not yet the full Reaper source-language parser/lowering for declarations and `each` statements. The DABI64 execution frame owns each value slot. Replacing a slot copies the new value before dropping the old one. Return, invalid branch, type error, failed I/O and step-budget exhaustion all converge on reverse-order frame cleanup. The program verifier checks slot indexes, call IDs, arities, auxiliary iterator outputs, branch targets and the presence of a return.

## ELF64 object writer and static linker

`reaper_elf64_write_object` serializes host-assembler-independent little-endian x86-64 `ET_REL` objects with PROGBITS/NOBITS sections, local/global/weak symbols, symbol/string tables and RELA sections.

`reaper_elf64_link` accepts multiple relocatable objects, resolves local and global/weak symbols across them, rejects duplicate strong definitions and unresolved strong externals, and applies `R_X86_64_64`, `PC32`, `PLT32`, `32`, and `32S` relocations. It emits a section-header-free static `ET_EXEC` with a read-only header load segment and page-separated load segments. W+X input sections are rejected. NOBITS segments have zero file size and retain their memory size for BSS zeroing.

Current linker limits: no archive extraction, COMDAT/group selection, common-symbol allocation, GOT/PLT generation, dynamic relocation, shared-library support, TLS, unwind metadata, or linker scripts. Sections are laid out as independent load segments rather than merged by name.

## ELF loader and initial stack

`reaper_elf64_plan_load` validates ELF64 little-endian x86-64 static `ET_EXEC` images: header/table bounds, PT_LOAD ranges, file/memory sizes, alignment congruence, non-overlapping virtual ranges, no W+X, and an entry point inside an executable segment. It rejects PT_INTERP and PT_DYNAMIC.

`reaper_elf64_apply_load` uses an OS-provided map/protect/release callback. It copies file bytes, zeroes the `p_memsz - p_filesz` tail, then applies final permissions. The caller owns and destroys the address space after failure or process exit.

`reaper_elf64_build_initial_stack` builds argc, argv, envp and a minimal auxv (`AT_PAGESZ`, `AT_ENTRY`, `AT_NULL`) in a caller-provided stack mapping and returns a 16-byte-aligned stack pointer.

## DABI64 process entry bridge

`reaper_dabi_process_dispatch` initializes a process-owned DABI64 runtime and calls a typed ABI-v1 entry trampoline with argc/argv/envp. It reports the exit code and refuses successful teardown if the entry returns with live owned runtime objects. The loaded address space itself is still owned by the OS caller; this typed function pointer is a host/runtime trampoline, not yet a ring-3 context switch or direct ELF instruction dispatch.

## Tests

CMake/CTest currently contains dedicated tests for:

- DABI64 value/ownership/I/O contracts and iterator-mediated cycle rejection.
- Runtime-call program execution, `each` iteration, canonical integer IR lowering, I/O error cleanup and step/branch validation.
- ELF64 section/symbol/RELA writer validation.
- Multi-object static symbol resolution, relocation application, duplicate-strong and unresolved-symbol rejection, W+X rejection.
- ELF64 PT_LOAD validation, BSS zeroing, memory callback protection and initial-stack layout.
- DABI64 process entry and clean runtime teardown.

Run the native C17 suite with `cmake -S . -B build -DREAPER_BUILD_TESTS=ON`, `cmake --build build --parallel`, then `ctest --test-dir build --output-on-failure`.

## Remaining gates

1. Extend canonical IR and the source parser/lowerer to represent text/collection values, calls, control-flow blocks and `each` directly.
2. Add CFG liveness/ownership analysis so compiler-emitted drops are explicit at every basic-block edge, not only covered by the whole-program cleanup frame.
3. Emit native x86-64 instructions and ELF relocations from verified DABI64 program IR; connect object generation to the linker.
4. Add kernel-backed address-space callbacks and ring-3 entry/exit, per-process descriptor ownership, syscall validation, and process reaping.
5. Boot DuckOS with the Reaper runtime, execute a Reaper-written stage-0 component, then complete Stage 1/Stage 2 clean-room bootstrap.

The Python runtime remains the compatibility oracle until differential language conformance passes. Ivan-VHS is the project author/developer; preserve all third-party notices and upstream contributor attribution.
