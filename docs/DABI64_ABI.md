# Reaper DABI64 v1

Status: versioned C ABI contract and validation shim implemented. Platform dynamic loading and native code generation for this ABI are separate integration gates.

## Contract

A DABI64 v1 module exports the descriptor entry point named reaper_dabi64_module_v1. The host validates ABI version, descriptor size, module name, invoke callback, argument count, and tagged-value invariants before calling the module.

The value record is a fixed 24-byte structure: 32-bit kind, 32-bit flags, 64-bit payload, and 64-bit length. I64 values are passed by value. UTF-8 and byte strings use a pointer plus byte length. UTF-8 payloads are validated for correct encoding, excluding overlong sequences, surrogate encodings, truncated sequences and code points above U+10FFFF. I64 arrays use a pointer plus element count. Opaque handles are module-defined.

Owned pointer-bearing results are released only through the host-provided release callback. Scalar results do not require release.

## Safety and compatibility

- Fixed-width integers and compile-time layout assertions are part of the public header.
- The host and module must agree on ABI version 1 and the complete v1 structure sizes.
- Calls reject more than 4096 arguments; strings and byte slices are bounded to 1 MiB; arrays are bounded to 100,000 elements.
- The callback uses the C ABI. This does not promise C++ exception unwinding or compatibility with a Rust-specific ABI.
- Native modules execute with process privileges. Only trusted libraries should be loaded from explicitly selected absolute paths.
- 32-bit targets are rejected at compile time.

## Current integration boundary

The public C header, validation shim and CTest coverage are part of the Reaper native core. The scalar AOT compiler does not yet generate DABI64 module descriptors, load DLL/SO/DYLIB files itself, or lower every native source value to this tagged representation. That connection requires the next backend milestone and platform-loader tests.
