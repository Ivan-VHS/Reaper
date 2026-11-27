# Reaper Processor Engineering Platform v1

**Status:** first host-oriented vertical slice under review; full processor-target code generation is not implemented.
**Canonical project manifest:** `reaper.processor-project/v1`
**Manifest schema:** `schemas/processor-project.v1.schema.json`
**Reaper policy module:** `stdlib/processor_workbench.rpr`
**Pytyliki evidence:** `pytyliki.report.v1`
**Executable fixture:** `examples/processor-workspace/processor_workbench.rpr`

## Purpose

The **Reaper Processor Engineering Platform (PEP)** organizes existing Reaper systems-language, Typed Registry, hardware contracts, scalar AOT path, resource controls and diagnostics into a coherent processor-development workflow.

Pytyliki remains the native C11 processor-systems workstation. It supplies read-only CPU discovery, OS-usable ISA state and bounded host benchmark evidence. Reaper owns processor project descriptions, target/ABI contracts, source orchestration, workload policy, result reconciliation and reproducible engineering reports.

This is a platform direction with a concrete first slice, not a claim that a full CPU compiler, assembler, linker, simulator or hardware debugger already exists.

## Ownership boundaries

| Area | Reaper owns | Pytyliki owns |
|---|---|---|
| Processor project | Versioned project manifest, target constraints, workload and verification policy | Consumes project intent only through published interfaces |
| Language and compiler | Reaper syntax/semantics, Typed Registry, canonical IR roadmap, native AOT subset and source diagnostics | Native C11 processor inventory and measurement implementation |
| CPU architecture | Declarative target architecture, ABI, endianness, memory contract and required ISA | Actual host CPU/vendor/model, logical processor count and OS-usable ISA evidence |
| Build and verification | Source checks, scalar C17 AOT orchestration, project report and future build graph | Bounded CPU, memory and matrix workloads plus measurement integrity |
| Hardware | Typed MMIO/effect/capability contracts and future host-adapter boundary | Read-only host inspection, platform evidence and processor-specific measurement |
| Privileged actions | No implicit privileges; future OS/driver adapters must own them | No implicit register, firmware, microcode, voltage or frequency writes |

A Pytyliki host report is not proof that an arbitrary target board or processor matches the host. Reaper preserves that distinction in every build report.

## Platform layers

1. **Processor project contract.** A machine-readable manifest records project identity, target triple, architecture, ABI, address width, endianness, required ISA features, memory budgets, workload bounds, compiler backend, sources and verification policy.
2. **Typed target model.** The existing Reaper Typed Registry validates scalar layouts and platform/ABI tuples. The workbench example validates an x86-64 System V host target through that registry.
3. **Host evidence.** Pytyliki produces `pytyliki.report.v1` with CPU identity, logical processors, memory, usable ISA flags and bounded benchmark runs. Reaper validates the report before using it.
4. **Workload and resource admission.** Reaper rejects missing ISA support, insufficient logical processors or memory, malformed benchmark history, failed integrity flags and runs outside the declared workload envelope.
5. **Compilation.** The current compiler path is the narrow Reaper scalar AOT subset: `.rpr → checked scalar C17 → installed host GCC/Clang-compatible compiler → host executable`.
6. **Evidence report.** Reaper writes `reaper.processor-workbench-report.v1`, preserving target identity, host profile, benchmark provenance, compiler maturity and explicit false hardware-effect flags.
7. **Future toolchain stages.** HIR/MIR/LIR processor intrinsics, target instruction selection, assembly emission, object writing, linking, disassembly, simulator/debugger and hardware qualification remain separately gated milestones.

## Project manifest

The checked-in sample is `examples/processor-workspace/x86_64-linux.project.json`. It intentionally selects:

- x86-64, 64-bit little-endian and SYSV64;
- SSE2 as the required ISA floor;
- an explicit available-memory minimum and bounded working set;
- a scalar C17 host-only backend, with `target_qualified=false`;
- a bounded scalar probe with fixed workload parameters;
- integrity checks and deterministic replay requirements.

The manifest schema rejects unknown fields, unsupported ISA names, unbounded resource values, absolute or traversal-bearing source/output paths, DMA use in the host-only scalar profile and unsupported backend claims.

The Reaper module applies the key cross-field rules during execution. The JSON Schema is the interchange contract; the Reaper module is the executable policy implementation for the reference runtime.

## Pytyliki evidence workflow

Generate the producer report from the machine that will run the workbench:

```sh
./pytyliki --profile --suite --repeat 3 --json > build/pytyliki-processor-report.json
```

The report includes architecture, CPU vendor/model, logical processor count and available/physical memory; SSE/AVX/AES/FMA flags, with AVX usability dependent on OS-managed vector state; repeat/warm-up/measured runs, workload parameters, checksums, integrity flags, descriptive timing statistics and a host-dependence note.

Reaper does not compare raw benchmark milliseconds against a universal pass threshold. It checks that the suite is complete, finite, integrity-valid and within the declared workload envelope. Timing is evidence, not a guaranteed performance claim.

## Run the first workbench slice

From the Reaper repository root, with Pytyliki built locally and its report written to the path below:

```sh
cmake -S ../Pytyliki -B ../Pytyliki/build -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build ../Pytyliki/build --parallel --target pytyliki
mkdir -p build
../Pytyliki/build/pytyliki --profile --suite --repeat 3 --json > build/pytyliki-processor-report.json

python -m reaper --check examples/processor-workspace/processor_workbench.rpr
python -m reaper examples/processor-workspace/processor_workbench.rpr

python -m reaper examples/processor-workspace/scalar_probe.rpr --native build/processor-scalar-probe
./build/processor-scalar-probe
```

The sample is a host x86-64 project and is expected to reject a non-matching host rather than silently treating it as a valid cross target.

## What the first slice does not do

- It does not emit target-specific x86, ARM, RISC-V or Elbrus machine instructions.
- It does not generate assembly, ELF/PE/Mach-O object files or a firmware image.
- It does not invoke a linker script, flash a device or execute code on another processor.
- It does not map physical MMIO, configure interrupts or DMA, change CPU affinity, start/stop cores, control frequency/voltage, write firmware or update microcode.
- It does not claim that the installed host compiler is qualified for every target triple in the manifest.

The scalar probe verifies only the current Reaper scalar host AOT path. The Pytyliki report describes only the machine that generated the report. A target-specific build must remain blocked until its compiler, ABI, linker, ISA and runtime contracts are implemented and qualified.

## Development roadmap

| Stage | Capability | Acceptance gate |
|---|---|---|
| P1 | Processor project manifest, target/ABI description and Typed Registry validation | Positive/negative manifest fixtures, stable diagnostics |
| P2 | Pytyliki host evidence import and resource/ISA reconciliation | Real CI-generated report, missing-ISA and low-memory negative cases |
| P3 | Reaper scalar host AOT workflow and report export | C17 build, executable smoke test, deterministic report schema |
| P4 | Canonical processor HIR/MIR/LIR and architecture-neutral kernel IR | Typed IR verifier, spans, effect and ownership checks |
| P5 | ISA profiles, intrinsic contracts and instruction selection | Per-target legal/illegal lowering tests and cross-target fixtures |
| P6 | Assembly/object writer, linker and disassembly metadata | Reproducible object fixtures, ABI/layout/relocation tests |
| P7 | Simulator, trace/replay, debug adapters and hardware qualification | Deterministic simulator runs, signed toolchain/device evidence |
| P8 | Reaper Studio processor workspace | Target explorer, memory map, instruction/IR viewer, register and trace panels |

Each stage requires implementation evidence; adding a catalogue row or UI panel alone does not promote a capability to delivered.

## Safety and reproducibility

- Pytyliki inspection is read-only; Reaper consumes its caller-selected JSON file.
- The host evidence is local by default. No remote service or telemetry upload is required.
- Target ISA claims are checked against usable feature flags, not only hardware-presence bits.
- Toolchain commands are executed by the host CI/build layer, not implicitly by a `.rpr` expression.
- Native FFI remains opt-in and must use an explicit trusted library path.
- Generated reports record whether a capability was only declared, observed, compiled, simulated or hardware-qualified.
- No firmware, driver, microcode, BIOS/UEFI, register, affinity, voltage or clock operation is authorized by a project manifest.

The processor workbench is a compiler-and-evidence environment first. Privileged processor control remains a separate, explicitly granted platform service.
