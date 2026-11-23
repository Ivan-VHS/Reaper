# DABI64 v1 native runtime

Status: initial runtime substrate implemented; compiler and OS integration remain in progress.

## ABI contract

\`\`\`c
typedef struct {
    uint32_t tag;
    uint32_t flags;
    union { int64_t i64; double f64; uint64_t bits; void *object; } payload;
} ReaperDabiValue;
\`\`\`

The public value is 16 bytes on a 64-bit target. Runtime initialization rejects non-64-bit layouts, ABI-version mismatches and truncated host tables. The runtime is C17 and has no direct dependency on libc file APIs, POSIX descriptors or Windows handles. Allocation is injectable.

## Implemented

- Tagged unit, boolean, i64, f64, string, array, descriptor and iterator values.
- Reference-counted owned objects and explicit \`value_copy\` / \`value_drop\`.
- String allocation, byte view and concatenation.
- Dynamic arrays with push, indexed read and length.
- Iterator objects retaining their source array; \`iterator.next\` returns an owned value plus a separate completion flag.
- ReaperDabiFrame for compiler-managed temporary ownership. A code generator can register temporaries and insert drops on normal, return, break, continue and error edges.
- Host callback table for open/read/write/close and complete \`emit\`/\`file_write\` loops that handle partial writes.
- Stable runtime-call descriptors and dispatch for emit, strings, collections and iterators.

Arrays reject direct and indirect cycles, including an iterator that would retain the array it is inserted into. Iteration keeps a source alive even if the original local reference is dropped.

## Ownership rules

1. Constructors return one owned reference.
2. \`value_copy\` creates another owned reference for heap-backed values.
3. \`array_push\` stores an owned copy; the caller retains its own value.
4. \`array_get\` and \`iterator_next\` return owned copies.
5. \`value_drop\` is idempotent for a value already reset to unit.
6. A frame owns every value passed to \`frame_hold\`; \`frame_drop_all\` releases in reverse order.
7. Runtime destruction refuses to succeed while live objects remain.

Reference counting is intentionally simple for the first runtime slice. Cyclic object graphs are rejected rather than collected.

## Host I/O contract

The host supplies callbacks. A host callback returns zero on success and writes a byte count to its output parameter. \`write\` is permitted to complete partially; \`emit\` and \`file_write\` retry until all bytes are written, and reject zero-progress or oversized completions. \`read\` returns the number of bytes read (zero means EOF). \`open\` returns a host-owned descriptor and \`close\` releases it.

The runtime does not yet keep an internal descriptor registry; process-level descriptor ownership and close-on-exit must be connected to the compiler's resource scopes in the next integration step.

## Build and test

The runtime is part of \`reaper_core\` and has a dedicated native test executable:

\`\`\`sh
cmake -S . -B build -DREAPER_BUILD_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
\`\`\`

\`tests/test_dabi64.c\` exercises strings, collection ownership, cycle rejection, iterator lifetime, frame cleanup, partial host I/O, emit and dispatch. The test forces assertions on even in Release builds. The runtime was also tested with strict warnings and AddressSanitizer/UndefinedBehaviorSanitizer.

## Not yet implemented

- Lowering from canonical Reaper IR to DABI64 calls.
- Compiler-generated frame scopes and drop insertion across every control-flow edge.
- Lowering of \`each\` into iterator begin/next and per-item drop.
- UTF-8 validation policy and language-level string indexing semantics.
- Descriptor table ownership and automatic close at process exit.
- Native ELF writer/linker/loader, process entry dispatch and DuckOS kernel execution.
- Full C17 parity with the Python reference runtime.

Ivan-VHS is the project author/developer. Existing upstream contributors and third-party rights must remain attributed in their respective files.
