# Native typed import, host backend and Pytyliki bridge

## Scope

This change adds a verifiable import path for the currently supported scalar expression frontend and a first host C17 source-emission backend. It is not a complete Reaper module importer and does not introduce direct x86-64, AArch64, PE/ELF machine-code emission.

## Import manifest and verification

\`\`\`c
ReaperSourceImportManifest {
    module_id,
    generation,
    expected_generation,
    expected_source_digest[32]  // SHA-256
}
\`\`\`

The importer hashes the exact source byte sequence (no implicit NUL terminator), requires the declared generation to equal the expected generation, then runs the existing lexer, parser, scalar IR lowering and IR verifier. Output is staged in caller-owned bounded storage and published only when all checks pass.

Byte spans are UTF-8 byte offsets with half-open semantics [start,end). The lexer records the original source offsets, the parser combines child spans, and lowering copies them into Canonical IR. Line and column remain available for human-facing diagnostics.

The typed adapter currently represents:
- i64 values and unit return;
- pure scalar operations and the terminal control-flow return;
- ownership state NONE for the scalar subset;
- source spans and generation/digest identity.

The public effect and ownership enums reserve vocabulary for memory, MMIO, DMA, privileged and unsafe effects, and for borrowed/owned/moved/shared values. These effects and ownership states are not yet implemented as executable Reaper language constructs by this importer. Any non-represented type, effect or ownership state is rejected by the verifier.

The accepted source grammar is the existing native scalar expression subset: integer literals, parentheses and checked i64 \`+\`, \`-\`, \`*\`, \`/\`, including signed unary minus, followed by the frontend's return lowering. It is not the full Reaper language, module/import syntax, async/IRQ language, or complete ownership/region checker.

## Host C17 backend

\`\`\`c
reaper_backend_host_c17_emit(module, output, capacity, &written, &error)
\`\`\`

The backend emits deterministic C17 source for the checked scalar IR operations: constant, add, subtract, multiply, divide and return. It includes explicit overflow/division guards so generated C does not rely on undefined signed-overflow behavior.

The platform C compiler performs native machine-code generation, object format emission, relocation and calling-convention/ABI work. Therefore:
- \`REAPER_HOST_C17_BACKEND_ID\` is a source backend, not a native ISA emitter;
- \`native_machine_code\` remains false in its qualification report;
- \`abi_delegated_to_host_compiler\` remains true;
- qualification evidence is supplied by tests/harness and missing evidence is never inferred.

The golden fixture test compares generated C source byte-for-byte with the compiled fixture and checks execution against the Reaper IR interpreter. The additional arithmetic qualification test exercises the full currently supported scalar opcode set.

Direct x86-64 SysV, x86-64 Windows, AArch64 and DABI64 machine-code backends require their own implementations, ABI fixtures, relocation/link tests and qualification reports; they are not claimed complete here.

## Build and test

Normal Reaper native test build:

\`\`\`sh
cmake -S . -B build -DREAPER_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
\`\`\`

## Opt-in Pytyliki hardware bridge

The bridge accepts function pointers supplied by the application. It does not dynamically load a library, request privileges, execute MMIO/DMA, or change thread/process affinity.

Configure with the Pytyliki C headers and its real FFI library:

\`\`\`sh
cmake -S . -B build-native \
  -DREAPER_BUILD_TESTS=ON \
  -DREAPER_ENABLE_PYTYLIKI_HARDWARE_BRIDGE=ON \
  -DREAPER_PYTYLIKI_INCLUDE_DIR=/path/to/Pytyliki/src \
  -DREAPER_PYTYLIKI_LIBRARY=/path/to/libpytyliki_ffi.so
cmake --build build-native --parallel
ctest --test-dir build-native --output-on-failure
\`\`\`

The bridge verifies provider ABI version, native snapshot contract version and structure size, topology generation/fingerprint, array bounds, candidate ordering and the selected candidate. It only returns a placement proposal; applying processor affinity is a separate caller-owned operation.

## Qualification boundaries

Automated CI can qualify the Linux APIs and the Windows APIs visible on their respective hosted runners. Hosted VMs may expose virtualized topology and do not prove bare-metal NUMA/cache/performance accuracy on another machine. Dynamic bandwidth/cache counters remain optional caller-supplied telemetry, not values fabricated by the collector. Real DMA mapping, IOMMU programming, hardware fences and device reset remain the responsibility of a future platform DMA adapter and are not part of this validator's pure state model.
