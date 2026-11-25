# Reaper system runtime contracts

**Contract:** `reaper.system-runtime.v1` · **C ABI:** `REAPER_SYSTEM_RUNTIME_ABI = 1`  
**Status:** Partial — 20 stable operation contracts and bounded native validators; no privileged operation dispatcher.

This layer brings the requested service, hardware, AI, isolation, virtualization, package and cross-target operations into the Reaper native core without pretending that a C catalogue is an operating system. The registry is additive: it does not replace the language grammar, Canonical IR, the existing capability suite, or the checked MMIO API.

## Operation map

| ID | Subsystem | Operation | Native state |
|---:|---|---|---|
| 111 | System services | `service.daemonize` | Adapter contract |
| 112 | System services | `service.lifecycle_hooks` | Adapter contract |
| 113 | System services | `scheduler.cron_schedule` | Numeric cron validator |
| 114 | System services | `logging.append` | Bounded SPSC queue |
| 115 | System services | `service.start_unit` | Stable dependency ordering |
| 116 | System services | `system.graceful_shutdown` | Adapter contract |
| 117 | System services | `system.emergency_mode` | Adapter contract |
| 118 | Hardware services | `device.handle_event` | Adapter contract |
| 119 | Hardware services | `firmware.load` | Bounds + signature callback |
| 120 | Hardware services | `acpi.parse` | ACPI length + checksum validation |
| 121 | AI runtime | `ai.npu_initialize` | Adapter contract |
| 122 | AI runtime | `ai.tensor_matmul` | Tensor shape/type/storage validation |
| 123 | AI runtime | `ai.inference` | Adapter contract |
| 124 | AI runtime | `ai.model_load_onnx` | Adapter contract |
| 125 | AI runtime | `ai.private_inference` | Reviewed HE backend required |
| 126 | Isolation | `container.create` | Isolation-policy validation |
| 127 | Virtualization | `virtualization.create_vm` | VM profile validation |
| 128 | Packages | `package.install_sandboxed` | Signed manifest validation |
| 129 | Packages | `package.install` | Signed manifest validation |
| 130 | Build infrastructure | `build.cross_compile` | Target identity validation |

The machine-readable catalogue lives in `language/system-runtime.v1.json`; its schema is `schemas/reaper.system-runtime.v1.schema.json`. The C17 registry in `include/reaper/system_runtime.h` and `src/system_runtime.c` is the native query surface.

## Native C17 API

The registry exposes `reaper_system_operation_count/at/find` and `reaper_system_authorize`. Authorization checks all four dimensions before an adapter may be considered: canonical registry ownership, exactly one runtime profile, the complete required effect set and the required adapter bit. A copied or caller-forged operation descriptor is rejected.

**Authorization is not execution.** Every entry currently returns `dispatchable = 0`. The registry has no privileged syscall trampoline, daemon launcher, power controller, driver loader, NPU command queue, ONNX executor, homomorphic evaluator, container creator, hypervisor or package installer.

Implemented bounded primitives:

- `reaper_system_cron_validate`: validates five numeric cron fields, lists, ranges and positive steps. Month/day names and timezone policy belong to a scheduler adapter.
- `reaper_system_dependency_order`: deterministic Kahn ordering for up to 256 nodes; rejects malformed matrices and cycles without partially modifying the output.
- `reaper_system_log_ring_*`: fixed-storage single-producer/single-consumer queue with acquire/release publication. Capacity reserves one slot; it does not persist, rotate or encrypt logs.
- `reaper_system_acpi_table_validate`: checks the standard ACPI header size, declared length, caller limit and byte checksum. It does not discover RSDP, map physical tables or execute AML.
- `reaper_system_firmware_verify`: checks bounded image input and delegates signature verification to an explicitly supplied trusted verifier. No cryptography is implemented here and no firmware is flashed.
- `reaper_system_tensor_matmul_validate`: checks dimensions, supported element format, overflow-safe storage sizes and output capacity. It does not perform matrix multiplication or DMA.
- `reaper_system_container_policy_validate`: requires user/mount/PID isolation, read-only root, no-new-privileges, seccomp and nonzero memory/CPU/process quotas; network access requires a network namespace.
- `reaper_system_vm_profile_validate`: validates the declared guest architecture, host virtualization availability, vCPU/memory bounds against an explicit 4–64 KiB power-of-two host base page size, and the IOMMU requirement for device passthrough.
- `reaper_system_package_manifest_validate`: checks package identifier, numeric `major.minor.patch` version, 64-hex image digest, manifest-size bound, rollback/isolation policy and an external signature-verifier callback.
- `reaper_system_target_validate`: validates a bounded target triple from x86_64, AArch64, RISC-V 64, e2k, ARMv7 or WASM32 families plus safe toolchain/sysroot identifiers. It does not launch a compiler.

## Adapter and privilege rules

- System services are owned by the OS service manager and init implementation. Reaper does not fork/detach a process as a substitute for an OS service contract.
- Device discovery and driver binding remain in the trusted device manager. Firmware mutation requires verified vendor provenance, device/architecture matching, signature verification, rollback and a dedicated driver adapter.
- ACPI mapping is kernel/boot-only. ACPI checksum success is not proof that table contents or AML are safe.
- CPU/GPU/NPU execution backends have separate capability and memory-coherency contracts. DMA mapping and completion are not inferred from a device address.
- Containers need kernel-enforced namespaces, cgroups/resource controls, mount policy, seccomp and capability isolation. `chroot` alone is not a sandbox.
- VM creation needs a real hypervisor API, vCPU loop, exit handling, guest memory lifecycle and a separately verified device-passthrough/IOMMU path.
- Package installation is not a shell command. Never interpolate package names into `system()`; use a package adapter with canonical manifests, signatures, atomic staging, rollback and downgrade policy.
- Cross compilation uses argument vectors and pinned toolchain identities. The API does not select GCC by default and does not call `make` through a shell.

No Linux-specific path such as `/dev/kvm` or `/dev/npu0` is part of the language contract. Linux adapters may be implemented as optional backends, but DuckOS uses its own ABI and subsystem contracts.

## Reaper source compatibility

`examples/system_runtime_inventory.rpr` is an executable Reaper reference-runtime example that reads and prints the catalogue metadata. It intentionally does not call privileged operations. The proposed typed/effect syntax for native service declarations remains a target-language design until grammar, type/effect checking, IR lowering and conformance fixtures are implemented.

## Build and verify

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --system-capabilities
./build/reaper-c --system-capability scheduler.cron_schedule
python -m reaper --check examples/system_runtime_inventory.rpr
python -m reaper examples/system_runtime_inventory.rpr
```

The native C tests exercise all 20 registrations, authorization denial paths, cron parsing, dependency cycles, ring capacity/order, ACPI checksums, firmware/package verifier callbacks, tensor validation, sandbox policy, VM profile limits and target identity parsing.
