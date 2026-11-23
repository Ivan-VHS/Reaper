# DuckOS host contract for Reaper DABI64 v1

This repository currently contains the ABI adapter contract and a host-stub test, not a bootable operating system. The bridge is designed to be implemented first by a mock host and then by DuckOS kernel syscall handlers.

## Files

- \`include/duckos/reaper_host_v1.h\` defines the syscall table and adapter to \`ReaperDabiHostV1\`.
- \`tests/test_reaper_host.c\` validates the adapter against a deterministic mock kernel.
- \`CMakeLists.txt\` can build that test when \`REAPER_SOURCE_DIR\` points at a Reaper checkout.

## Syscall ABI v1

The bridge uses a versioned table with fixed-width arguments. The initial syscall numbers are:

| Number | Name | Arguments |
|---:|---|---|
| 1 | write | fd, user buffer, length, written out |
| 2 | read | fd, user buffer, capacity, read count out |
| 3 | open | path pointer, path length, mode, fd out |
| 4 | close | fd |

The low-level syscall callback returns zero on success and a negative kernel error on failure. The host adapter normalizes this to the DABI64 host callback convention (zero/nonzero). User pointers are passed as 64-bit integer addresses. The eventual syscall dispatcher must validate the full user-memory range, permissions, overflow and process address-space mapping before dereferencing them.

## Build adapter tests

\`\`\`sh
cmake -S . -B build \\
  -DREAPER_SOURCE_DIR=/path/to/Reaper \\
  -DDUCKOS_BUILD_DABI64_TESTS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
\`\`\`

The test checks open/read/write/close and \`emit\` through the DABI64 adapter. It does not test actual syscalls, paging, ELF loading or hardware.

## Kernel integration order

1. Implement kernel-side validation/copy helpers for user buffers and paths.
2. Add the versioned syscall dispatcher and descriptor table per process.
3. Provide \`write\`, \`read\`, \`open\` and \`close\` handlers with explicit error codes.
4. Map descriptors to VFS objects, with per-process ownership and close-on-exit.
5. Add ELF64 loading and map the executable, stack, argv and environment.
6. Dispatch DABI64 entry with a validated runtime host table.

Do not expose kernel pointers directly to user space. The syscall bridge is a compatibility boundary, not a security boundary by itself.

Ivan-VHS is the DuckOS project author/developer. Keep third-party kernel, bootloader and filesystem notices intact when those components are integrated.
