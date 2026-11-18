# MCST Elbrus E2K and AETHER-ANAS profile

Status: **host detection implemented; native E2K compiler backend planned, not implemented**.

## What Reaper does today

Reaper 0.1 is a Python-hosted tree-walking interpreter. The command:

~~~sh
python -m reaper --target-info
~~~

prints JSON host metadata. If Python reports machine name e2k, E2K or Elbrus, the profile labels the host architecture as E2K and its execution model as VLIW. It also states that the active interpreter remains python-tree-walk and native_codegen is false.

This is not a cross-compilation selector, an LCC version probe, a silicon feature query or proof that the current Python build was compiled by MCST LCC.

## Verified MCST platform facts

- MCST's programming guide documents __e2k__ as the C preprocessor target macro and __LCC__ as the compiler major-version macro.
- The guide describes Elbrus as VLIW: the optimizing compiler analyses dependencies, schedules operations and emits wide instructions. It documents software pipelining for loops.
- The MCST SDK includes its LCC compiler and supporting assembler, linker, debugger and profiling tools; the LCC sources are not included in the SDK. Availability and compatibility depend on the target CPU and OS release.

References:
- [MCST effective programming guide — E2K target macros](https://dev.mcst.ru/book/chapter2.html)
- [MCST effective programming guide — VLIW architecture](https://dev.mcst.ru/book/chapter4.html)
- [MCST effective programming guide — software pipelining](https://dev.mcst.ru/book/chapter6.html)
- [MCST Elbrus SDK](https://www.mcst.ru/SDK)
- [MCST LCC compiler](https://www.mcst.ru/LCC)

## AETHER-ANAS mapping

| Specification concept | Reaper status and interpretation |
|---|---|
| 66 laws and 12 mathematical models | Design heuristics and review prompts, not physical laws or compiler constants. Claims need executable tests or measured evidence. |
| 666 constitutional rules | Project acceptance ledger; each rule requires an explicit conformance state and evidence before it is called implemented. |
| Semantic hypergraph | Planned typed IR. Reaper currently uses Python AST dataclasses; there is no persistent binary hypergraph or content-addressed build graph. |
| Strict types and Curry–Howard | Planned static type/effect analysis. Reaper 0.1 remains dynamically typed at runtime; no proof system exists. |
| RAII, linear ownership and arenas | Planned semantics/runtime work. Current Python garbage collection is part of the host and offers no hard real-time allocation guarantee. |
| FBIP / in-place updates | Potential optimisation only after aliasing and semantic equivalence are defined and tested. |
| Bounded channels and backpressure | Planned stream/concurrency semantics. The current interpreter is sequential and has no task scheduler. |
| E2K VLIW lowering and software pipelining | Planned native backend. Do not hand-code fixed issue widths or assume all chip generations share one execution profile. |
| MCST LCC and SDK | External vendor toolchain dependency for future native builds; its availability and licence are separate from Reaper's Apache-2.0 licence. |

## Staged backend architecture

1. Freeze language semantics and executable conformance tests independently of Python implementation details.
2. Define a versioned typed IR with explicit effects, ownership/lifetime metadata, source maps and deterministic serialization. Keep .rpr source files canonical and reviewable.
3. Implement an IR verifier and a portable reference execution path before target lowering.
4. Add an E2K target module only after defining the target ABI, calling convention, object format, relocation/linking and debug-information requirements.
5. Use the supported MCST LCC toolchain and its assembly/disassembly/profiling tools as a comparison baseline; do not fabricate instruction schedules from an undocumented fixed-width model.
6. Prove loop and memory dependencies before enabling software pipelining or any dependence-relaxation directive.
7. Run one shared semantic suite on Python interpreter, E2K emulator (where coverage is adequate) and real MCST E2K hardware. Publish the exact SDK, compiler, OS and CPU versions for each validation result.

Native E2K code generation, static type checking, hardware register access, memory-tag integration, deterministic arenas, FBIP, parallel execution and formal proofs remain unimplemented. The existing Apache-2.0 project licence is unchanged and does not relicense MCST tools.
