# Constitution of the Ducks — 666-rule implementation profile for Reaper

Status: normative language/runtime roadmap and acceptance profile. It does not claim that the 666 capabilities are implemented.

## Product boundary

Reaper is an independent, text-first, expression-oriented language. The current 0.1 line is a Python-hosted interpreter with a deliberately small grammar, explicit console effects, immutable bindings by default, explicit reassignment, data-flow composition and bounded execution quotas.

This profile applies the Constitution's intent to the language specification, lexer, parser, runtime, standard operations, CLI, tests and documentation. It does not pretend that an interpreter is already a native compiler, operating system, distributed runtime, GPU language, cryptographic sandbox or self-hosting toolchain.

## Conformance states

- Implemented — present on the reviewed branch and covered by tests/CI.
- Partial — a limited semantic foundation exists; the complete capability is absent.
- Planned — a future language/runtime feature with explicit acceptance criteria.
- Not applicable — outside Reaper's current product boundary; reconsider only through an explicit design decision.

A syntax example or roadmap paragraph is not evidence of implementation.

## Six-part crosswalk

| Constitution section | Rules | Reaper interpretation | Initial status |
|---|---:|---|---|
| I. Three-medium computing and execution ontology | 1–111 | Portable semantic model independent of the Python host, explicit execution effects, deterministic local runtime and future backend boundary. CPU/GPU/cloud/FPGA distribution is not present in 0.1. | Partial / Planned / N/A |
| II. Hydrodynamic clarity and transparency | 112–222 | Small grammar, explicit operator precedence, clear diagnostics, bounded execution, predictable CLI, tested examples, deterministic behavior and transparent costs. | Partial |
| III. Duck typing and type system | 223–333 | Runtime value kinds and explicit conversions exist; static inference, algebraic data types, ownership/linear types and compile-time proofs are not present. | Partial / Planned |
| IV. Effects and immune barrier | 334–444 | Explicit console operations, immutable bindings by default, explicit mutation, bounded inputs, safe error propagation and a clearly stated non-sandbox security boundary. | Partial |
| V. Flock concurrency | 445–555 | Current interpreter execution is sequential. Any future concurrency must be structured, bounded, cancellable and deterministic under tests. | Planned |
| VI. Freedom, ergonomics and creator's code | 556–666 | Readable syntax, one canonical grammar, complete language reference, offline-friendly standard library, stable compatibility policy, tests and reproducible Python-version support. | Partial |

## Language invariants for the current line

1. No hidden effects: ordinary expressions do not perform file, network, clock, process or hardware I/O. Console interaction remains explicit through documented operations.
2. Mutation is visible: make binds an immutable name; vary explicitly permits reassignment; change performs reassignment. New mutation forms require an explicit syntax and semantics proposal.
3. Flow is composition: :: passes the left value as the first argument; associativity and evaluation order are specified and tested.
4. Conversions are explicit: numeric, text and boolean values are not silently coerced. Conversion functions document failure behavior.
5. Execution is bounded: steps, call depth, collection items and generated text are limited. New recursive, iterative, parsing or allocation paths add quotas or prove a safe bound.
6. Errors are user-facing contracts: syntax, name, type/value and quota failures are distinguishable and tested. A failure is never silently converted to a successful value.
7. Host/runtime distinction: Python is the implementation host, not part of Reaper language semantics. Host exceptions are translated at the runtime boundary without leaking implementation details as language behavior.
8. No sandbox claim: the current interpreter is not a security boundary for hostile programs. Do not execute untrusted Reaper programs in a privileged process and do not market quota checks as OS isolation.

## Six constitutional domains — implementation requirements

### I. Execution ontology (1–111)
- Keep language semantics independent of Python implementation details.
- Define a backend interface only when a second backend is actually being built; preserve one conformance suite across interpreters/compilers.
- Keep clock, randomness, filesystem, network, process and hardware access as explicit effects if introduced.
- Distributed execution, transparent remote calls, GPU kernels, FPGA, kernel/driver and zero-copy cross-device memory are roadmap or not applicable to the current 0.1 interpreter.
- Determinism claims specify which inputs, host versions and effects are controlled.

### II. Clarity and transparency (112–222)
- Maintain a canonical grammar and precedence table; parser behavior must not depend on formatting or accidental whitespace.
- Keep diagnostics tied to source spans and primary causes.
- Preserve deterministic quotas and expose them consistently through CLI and Python API.
- Keep examples executable in CI and the language reference synchronized with lexer/parser/runtime behavior.
- Benchmark claims require repeatable workloads, host/version metadata and measured results.

### III. Type system (223–333)
- First formalize current dynamic value kinds and operator compatibility; do not imply static typing exists.
- Specify nothing and absence semantics explicitly; do not silently equate it with an uninitialized or missing value.
- Introduce algebraic result/error values and pattern matching only through a versioned grammar proposal with exhaustive tests.
- Any future static type checker is a separate, testable phase and preserves interpreter semantics.
- Ownership, lifetimes, dependent types and proof-carrying code remain research items until a concrete implementation and diagnostics exist.

### IV. Effects and safety (334–444)
- Preserve immutable-by-default bindings and explicit mutation.
- Keep external effects explicit and deny ambient access by default if/when file, network or process operations are introduced.
- Validate source size, token count, nesting, collection size, text growth and execution steps before expensive work.
- Translate host exceptions into stable Reaper diagnostics; never swallow quota or cancellation errors.
- State clearly that language-level quotas do not replace OS sandboxing, process isolation or permissions.

### V. Concurrency (445–555)
- Current execution is sequential; no parallelism claim is permitted.
- A future task/actor model specifies parent-child cancellation, bounded queues, backpressure, fairness, ordering, failure propagation and shutdown.
- Tests deterministically cover cancellation, queue saturation, repeated execution and race-sensitive semantics before enabling concurrency.
- Distributed actors, exactly-once delivery and CRDT semantics are not 0.1 capabilities.

### VI. Ergonomics and evolution (556–666)
- Keep syntax compact but unambiguous; every operator has one documented precedence and evaluation rule.
- Keep lexer/parser authoritative; examples in docs pass --check and execute in CI.
- Version grammar and standard-library changes; provide migration notes for breaking changes.
- Keep installation and tests reproducible across supported Python versions and useful offline.
- Dependencies remain minimal and auditable; no install-time code execution or hidden telemetry.
- Preserve user control: the interpreter does not modify source files, repositories or host configuration implicitly.

## Prioritized implementation sequence

1. P0 — map each rule ID to current source/test/evidence and assign Implemented, Partial, Planned or Not applicable. Do not inflate conformance percentages.
2. P1 — formalize grammar, precedence, evaluation order, values, nothing, mutation, conversion and error semantics; add parser/runtime conformance tests.
3. P1 — enforce source, token, nesting, list/range, text, step and call-depth quotas consistently; add adversarial boundary tests.
4. P1 — add source-span-aware lexer/parser/runtime errors with stable categories and no leaked Python tracebacks in normal CLI output.
5. P2 — document input/output kinds, complexity, allocation behavior and failure modes for every built-in operation.
6. P2 — generate bounded expressions and malformed inputs; preserve every discovered bug as a regression test.
7. P2 — version the language grammar and standard library; add migration tests before syntax or semantic changes.
8. P3 — prototype optional type/effect analysis without changing 0.1 runtime behavior; prove parity with interpreter tests.
9. P3 — after semantic conformance is stable, prototype bytecode/native/Wasm backends behind the same language test suite.
10. P4 — add concurrency/distribution only with explicit demand, measurable benefit, bounded resource model and deterministic semantics. GPU, FPGA, cloud and distributed execution remain separate projects until validated.

## Rule-range coverage ledger

| Rule IDs | Reaper acceptance evidence |
|---|---|
| 1–111 | Host-independent semantics, explicit effects and backend conformance; distributed/hardware capabilities marked Planned/N/A |
| 112–222 | Canonical grammar, diagnostics, quotas, executable docs and reproducible test runs |
| 223–333 | Precisely specified value kinds/conversions; type-checker tests only when such a phase exists |
| 334–444 | Explicit effect boundary, input quotas, stable errors and truthful non-sandbox statement |
| 445–555 | Sequential-execution disclosure; future concurrency contract and deterministic cancellation tests |
| 556–666 | Syntax/reference quality, versioning, offline behavior, dependency provenance and compatibility tests |

The six ranges cover every rule exactly once. Maintain a finer-grained rule-to-source/test mapping for every rule promoted to Implemented.

## Change acceptance checklist

- [ ] The PR names the affected constitutional rule IDs.
- [ ] Language grammar and runtime semantics are updated together where needed.
- [ ] Normal, malformed, boundary and quota-exceeded cases are tested.
- [ ] All examples touched by the change pass validation and execution in CI.
- [ ] New resource-consuming operations have explicit limits and failure semantics.
- [ ] No unsupported native, static typing, sandbox, hardware or distributed capability is claimed.
- [ ] Python 3.10, 3.11 and 3.12 CI pass on the exact PR head.
- [ ] Compatibility and migration implications are documented.

A constitutional rule is not implemented because it is listed here. Implementation requires executable behavior, tests and CI evidence.
