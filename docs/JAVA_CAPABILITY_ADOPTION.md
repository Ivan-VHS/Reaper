# Java capability adoption for Reaper

**Project:** Reaper  
**Status:** architecture proposal and staged adoption plan  
**Baseline reviewed:** `main`, 2026-11-25  
**Reference platform:** Java SE / OpenJDK 25 LTS and Java SE 26  
**Implementation rule:** independent Reaper implementation; no JVM dependency

## 1. Decision

Reaper will study and selectively reimplement the useful capabilities demonstrated by the Java language, JVM/JDK platform and Java development ecosystem. This is a capability-adoption programme, not a Java clone, a JVM fork, a Java syntax mode or a promise to embed every Java library.

Reaper keeps its own language identity and contracts:

- `.rpr` remains the source format and existing source programs retain their current meaning.
- Reaper owns its grammar, names, semantics, type system, standard library, compiler IR, diagnostics and package format.
- The canonical language surface remains flow-first and supports the established Reaper operators and forms. Java-like features must be expressed in Reaper syntax after an explicit language-design decision; Java keywords and class names are not imported by default.
- The long-term compiler direction is a canonical typed IR with source spans and source maps, a Reaper bytecode/VM route where it provides value, and native AOT backends. DABI64 is a Reaper-owned ABI contract, not a copied JVM or JNI ABI.
- Existing reference-runtime behavior remains the compatibility oracle until differential tests prove parity for a construct on another engine.
- No feature is considered implemented merely because it appears in a registry, syntax highlighter, document, generated catalogue or roadmap.

**Non-goal:** reproducing the entire Java SE API, Java class-file format, HotSpot, garbage collector internals, class-loader model or enterprise framework catalogue. These are independent implementations with different trade-offs and licensing constraints. Reaper should adopt the capabilities and engineering lessons that solve Reaper/Dak OS problems.

## 2. Evidence-based baseline

The repository currently documents a Python reference runtime, conservative but partial static type analysis, a partial native C17 compiler path, explicit host FFI, and separate hardware/QCS contracts. Its polyglot capability layer already lists Java as one of several capability references. In that inventory, user generics are partial, interfaces/protocols and algebraic data types are planned, language-level async/structured concurrency is not yet implemented, and native compilation is experimental. This proposal extends that existing design; it does not relabel those capabilities as complete.

Before implementing each feature, update the relevant evidence in `docs/FEATURES.md`, `docs/POLYGLOT_CAPABILITY_LAYER.md`, the machine-readable feature registry and the tests. Preserve the distinction between reference-runtime support, compiler support, host integration and target-specific support.

## 3. Java baseline for the 2026 review

The review uses two different Java baselines, not an arbitrary mixture of preview and stable features:

- **Java 25** is the current LTS baseline in the reviewed Oracle release information.
- **Java 26** is the current feature-release baseline. Its published feature set includes HTTP/3 support in the HTTP client, primitive patterns in preview, lazy constants in preview, structured concurrency in preview, and the Vector API in incubator status. It also includes GC and ahead-of-time cache improvements.

Important Java 25 capabilities to study include module import declarations, compact source files and instance main methods, flexible constructor bodies, scoped values, structured concurrency, stable values, compact object headers, AOT method profiling, and JFR observability. Preview/incubator status is part of the evidence: it is not a reason to copy an unstable API wholesale.

Reference release notes:
- [Java downloads and release status](https://www.oracle.com/java/technologies/downloads/) — current feature and LTS release families.
- [JDK 25 release notes](https://www.oracle.com/java/technologies/javase/25all-relnotes.html)
- [JDK 26 release notes](https://www.oracle.com/java/technologies/javase/26all-relnotes.html)
- [Java 26 announcement](https://www.oracle.com/news/announcement/oracle-releases-java-26-2026-03-17/)

For every future review, record the source release, publication date, JEP/API status, compatibility impact and whether the capability is stable, preview, incubating, deprecated or removed. Do not treat preview or incubator features as stable standards.

## 4. Capability portfolio

Each entry below is an investigation and design target. It becomes an implementation commitment only after a Reaper design decision, contract, test plan and target boundary have been accepted.

### 4.1 Language model and type system

Study and adapt:

- primitive and value types, signed/unsigned widths, fixed-width integers, floating-point rules and explicit numeric conversions;
- user-defined product and sum types, records/value records, enums and sealed variants;
- interfaces/protocols/traits, default behavior, composition and explicit dispatch;
- generic functions and types, bounded constraints, variance where sound, inference and specialization;
- lambdas, closures, function references, higher-order functions and capture rules;
- pattern matching, destructuring, exhaustiveness checks, guarded branches and expression-valued selection;
- visibility, namespaces, modules, package boundaries and explicit exports;
- attributes/annotations as structured compile-time metadata;
- reflection only through constrained metadata APIs, not unrestricted runtime mutation;
- source-level documentation contracts and generated API references.

Reaper-specific requirements:

1. Add source-level type declarations and generic constraints to the existing conservative checker without silently changing inferred legacy behavior.
2. Represent records, variants, interfaces and generic instantiations in one canonical semantic model.
3. Define variance, method dispatch, visibility and ABI layout in written rules before backend work.
4. Use specialization/monomorphization for predictable native performance where appropriate; do not inherit Java type erasure merely for surface similarity.
5. Make pattern matching exhaustive where the scrutinee type is closed, with diagnostics that carry `Span` and SourceMap data.
6. Keep compile-time metadata deterministic and inspectable.
7. Add a flow-friendly standard library; do not transplant Java Streams as an allocation-heavy wrapper. Optimize Reaper pipelines with fusion and explicit allocation behavior.

Do not add a new keyword until an ADR documents its spelling, parsing conflicts, MOST/localization implications, formatter behavior and compatibility strategy.

### 4.2 Memory, object model and resource lifetime

Study Java's object model, object layout, escape analysis, compact headers, allocation strategies, garbage collection and safe publication. Adopt the useful outcomes, not a mandatory managed heap everywhere.

Use explicit execution profiles:

| Profile | Intended policy |
|---|---|
| `kernel` / `firmware` | no implicit allocation, explicit ownership/borrowing, bounded stack, no collector or hidden scheduler |
| `native` | deterministic ownership and destruction by default; opt-in arenas/regions and bounded allocators |
| `desktop` / `service` | optional managed heap and collector when measured to be beneficial |
| `sandbox` | capability-bounded resources, quotas, safe handles and auditable allocation |

Required capabilities:

- ownership, borrowing, regions, lifetimes, move semantics and deterministic cleanup;
- arena, pool, slab and general allocator interfaces with explicit budgets;
- safe references, nullable/optional references and checked pointer arithmetic;
- escape/lifetime analysis, stack allocation and scalar replacement;
- compact value layouts and cache-aware collections;
- optional tracing, generational and concurrent collection for application profiles only after latency and memory benchmarks;
- allocation tracing, leak diagnostics and memory pressure observability.

A garbage collector must never be silently enabled in an interrupt handler, boot path, kernel subsystem or `no_alloc` function. GC and deterministic ownership are complementary profile-specific tools, not mutually exclusive ideologies.

### 4.3 Concurrency and parallel execution

Java's virtual threads, structured concurrency and scoped values provide useful design references. Reaper must define its own task and memory model.

Adopt, in stages:

- structured task scopes with child-task ownership, join, failure propagation and cancellation;
- lightweight tasks for high-concurrency I/O workloads, with a bounded scheduler and explicit backpressure;
- scoped immutable context values with well-defined inheritance;
- async I/O, futures/promises and composition through Reaper's typed result model;
- channels, bounded queues, select-like coordination and actor/mailbox patterns where they fit;
- atomics, locks, read/write synchronization, condition variables and memory-order rules;
- task-local tracing/request context without unbounded implicit global state;
- cooperative cancellation, deadlines, timeouts and resource cleanup;
- deterministic test scheduling, replay hooks and race-focused test fixtures.

Rules:

- A virtual/lightweight task is a scale mechanism, not a promise of lower single-task latency.
- CPU-bound work must use measured parallel execution; I/O-bound work may use a large number of lightweight tasks.
- Every queue, task group and scheduler has capacity limits and overload behavior.
- Cancellation must release or transfer owned resources exactly once.
- Kernel/IRQ/firmware profiles do not inherit a user-space task scheduler.
- Data races, memory ordering and FFI thread-safety are part of the language contract, not documentation footnotes.

### 4.4 Compiler, IR, VM and optimization

Learn from `javac`, HotSpot, JIT profiling, AOT caching and managed-runtime optimization, while retaining a native-first target strategy.

Target compiler pipeline:

```text
.rpr source
  -> lexer / parser
  -> AST + Span + SourceMap
  -> name resolution and typed semantic model
  -> HIR -> MIR -> LIR
  -> verified Reaper bytecode OR native backend
  -> object / executable / target image
```

The pipeline must have:

- canonical, versioned IR schemas and explicit verifier rules;
- deterministic lowering and stable diagnostic provenance;
- explicit effects, ownership, regions and target data layout;
- optimization passes with before/after IR dumps and source mapping;
- constant folding, propagation, dead-code elimination, common-subexpression elimination, inlining and devirtualization where proven safe;
- escape analysis, loop transformations, scalar replacement and vectorization where supported;
- profile-guided optimization based on recorded, reproducible training inputs;
- link-time optimization and incremental compilation where the target toolchain supports them;
- AOT cache invalidation tied to compiler, target, ABI, configuration and dependency identities;
- optional tiered/JIT execution only as an application-runtime capability, never a boot or kernel prerequisite;
- a Reaper bytecode verifier and versioned VM format if the VM path is selected.

A JVM, Java class-file compatibility and HotSpot bytecode are not required. Native object generation, ELF/PE/Mach-O output, linking and loading remain distinct deliverables with independent tests. Do not claim direct object generation while a host C compiler performs that step.

### 4.5 Standard library and platform APIs

Build a coherent, versioned Reaper standard library, grouped by capability and supported target:

| Domain | Reaper target capability |
|---|---|
| Core | text, Unicode, scalar values, ranges, iterators, formatting, errors, reflection metadata |
| Collections | vectors, lists, maps, sets, queues, heaps, immutable views, iterators and allocation-aware pipelines |
| Numeric | checked arithmetic, big integers/decimal as optional modules, math, complex numbers, SIMD/vector interfaces |
| Time | monotonic clock, wall clock, durations, calendar/time-zone data, timers and deadlines |
| Filesystem | paths, streams, buffered I/O, directory operations, file metadata and safe temporary files |
| Networking | sockets, DNS, TLS, HTTP clients/servers, WebSocket and HTTP/2/HTTP/3 through target adapters |
| Data | explicit schema serialization, parsers, compression, archive APIs and bounded streaming |
| Security | cryptographic provider interfaces, key handling, hashing, signatures, TLS policy and algorithm agility |
| Process | explicit process capabilities, environment access and controlled standard streams |
| Observability | structured logs, metrics, tracing, profiling events and crash diagnostics |

Java's NIO/channel/buffer model is a useful reference for scalable I/O and zero-copy boundaries. HTTP/3 is a current Java 26 feature to include in the networking evaluation. Reaper must keep protocol implementations in vetted, license-reviewed components and must not write bespoke cryptography.

Serialization must be schema-explicit, size-bounded, versioned and safe against gadget-style object construction. Do not provide an unrestricted native object deserializer.

### 4.6 Modules, dependencies and packaging

Adapt the mature package/build concepts associated with Maven, Gradle, JLink and JPackage without requiring their formats or runtimes.

Create a Reaper-native package model with:

- module manifests, explicit exports/imports and dependency constraints;
- semantic versions, compatibility ranges and a deterministic lockfile;
- local-first cache, offline builds and explicit registry configuration;
- dependency graph resolution with cycle and conflict diagnostics;
- reproducible source and binary builds, pinned toolchains and hermetic build options;
- package signing, checksums, SBOM and license/provenance metadata;
- dependency vulnerability reporting and update policy;
- target profiles and minimal runtime images containing only required capabilities;
- install/uninstall/upgrade transactions with rollback and integrity checks;
- opt-in package repositories; no hidden network access or implicit dependency installation.

Package management must preserve the ability to build Dak OS and core Reaper components in an offline environment.

### 4.7 Developer tooling and observability

Build equivalent capabilities for Reaper Studio, CLI and editor integrations:

- compiler diagnostics with structured codes, source spans, notes and fix suggestions;
- formatter, linter, refactoring and import/module organizer;
- LSP completion, hover, definition/references, semantic tokens, diagnostics and workspace symbols;
- DAP breakpoints, stepping, call stacks, locals, watches, exception stops and target debugging;
- interactive REPL and project-aware scratch execution;
- API documentation generator and source-level examples;
- test runner with unit, integration, property-based, fuzz, golden IR/Span and differential tests;
- benchmark harness that records hardware, compiler, flags, warmup, sample distribution and variance;
- low-overhead flight-recorder-style tracing, CPU/allocation profiling and timeline inspection;
- build/diagnostics cache with explicit invalidation and provenance;
- static analysis for unsafe code, effects, ownership, permissions and dependency risks.

Monitoring must not require a permanent high-overhead profiler. Diagnostic collection must be local-first, opt-in where data leaves the process and redact secrets by construction.

### 4.8 Security, trust and supply chain

Apply the strongest lessons from Java platform hardening:

- capability-oriented access control, sandboxed module execution and least privilege;
- strong module encapsulation and explicit unsafe boundaries;
- safe initialization and immutable-after-publication state;
- secure defaults for TLS, algorithms, keys and randomness;
- explicit crypto-provider selection and algorithm agility, including post-quantum readiness as a migration capability;
- strict validation of package signatures, manifests and dependency sources;
- memory/resource limits, decompression limits and parser depth limits;
- secure deserialization and process isolation;
- signed build provenance, SBOM, vulnerability and license scans;
- reproducible security updates and an auditable deprecation/removal process.

No network, filesystem, process, clock, environment, FFI or hardware permission is granted implicitly to ordinary Reaper code. Privileged access must be capability-granted and observable.

### 4.9 Java ecosystem patterns

Review frameworks and tools by capability rather than importing whole frameworks:

- dependency injection/configuration and service lifecycle;
- HTTP service routing, middleware and validation;
- reactive/backpressure patterns and asynchronous streams;
- persistence abstractions, transaction boundaries and migration tooling;
- messaging/event-driven services and RPC;
- plugin/provider discovery with signed manifests and versioned ABI;
- testing, mocking boundaries, contract tests and benchmark practice;
- data-processing pipelines and batch execution.

A candidate from Spring, Jakarta EE, Micronaut, Quarkus, Vert.x, Netty, Kafka, Hadoop, JUnit, Maven or Gradle is a reference for a specific Reaper problem. It is not automatically a dependency or a requirement to reproduce an entire ecosystem. Evaluate maintenance, security, license, footprint, offline behavior and value to Dak OS before accepting a capability.

### 4.10 Java interoperability as an optional adapter

Existing Java applications and libraries may remain useful during migration, but interoperability is not the Reaper execution model.

- Prefer a documented process/IPC boundary or a narrow native C ABI when a stable native library exists.
- Where an application genuinely requires a JAR/JVM dependency, use an explicit, separately deployed sidecar/host adapter with its own JVM version, permissions, dependency lock and license inventory.
- Define schema-based value conversion, ownership transfer, timeout, cancellation, error and shutdown behavior at the boundary.
- Never let Reaper silently load arbitrary JARs, execute Java code, start a JVM, download dependencies or inherit the sidecar's permissions.
- Bytecode/class-file compatibility, JNI and direct JVM embedding require separate proposals and acceptance criteria. They are not implied by this plan.

### 4.11 Application and framework patterns

For application-layer productivity, evaluate the useful ideas from dependency injection, inversion of control, configuration profiles, lifecycle hooks, routing, middleware, declarative validation, service discovery and observability. Reaper should express these as small composable packages with explicit effects and typed contracts. They must remain optional and must not enter kernel/firmware builds by default.

## 5. Mapping to Reaper and Dak OS

| Java capability | Reaper-owned implementation direction | Dak OS boundary |
|---|---|---|
| Generics, records, sealed types, pattern matching | typed AST/HIR, generic constraints, enum/record lowering, exhaustive diagnostics | app and service code; kernel subset only where bounded |
| Modules and service loading | signed Reaper package/module manifest and provider registry | Jora packages and Dak service manager |
| Virtual threads / structured concurrency | lightweight tasks, scoped task groups, cancellation and bounded scheduler | user-space services only; no implicit kernel scheduler |
| NIO/channels and HTTP client | Reaper I/O contracts and explicit OS adapters | Dak networking/filesystem services |
| FFM / JNI principles | safe C ABI plus Reaper-owned DABI64, typed handles and explicit unsafe FFI | Dak ABI, MMIO/DMA/IRQ adapters with capability gates |
| JIT/AOT, GC optimization | native AOT, IR optimizer, optional managed app runtime | native system apps; optional managed application profile |
| JFR/JMX observability | local event recorder, metrics, traces and profiler | Reaper Studio and Dak diagnostics |
| Maven/Gradle/JLink/JPackage ideas | offline package/build graph, lockfiles and minimal runtime bundles | Jora store and Dak package manager |
| Java crypto and trust APIs | vetted providers, TLS policy, signing and algorithm agility | BAV and OS trust services through versioned contracts |

Every row is an integration boundary, not a claim that the Dak-side subsystem already exists. Reaper must expose versioned contracts and test adapters before claiming cross-repository integration.

## 6. Clean-room and licensing policy

The Reaper repository is licensed under Apache-2.0. OpenJDK source is generally distributed under GPLv2 with the Classpath Exception, while Oracle JDK distributions have separate licensing terms. These are not interchangeable permissions.

Required controls:

1. Do not copy/paste OpenJDK, Oracle JDK, third-party Java framework or library source into Reaper.
2. Do not copy substantial documentation, examples, test suites, implementation comments, proprietary assets or generated files without an explicit license basis and attribution review.
3. Use public standards/specifications and independently written behavioral descriptions as design references. Write Reaper code and tests independently.
4. Keep a provenance record for every imported dependency, algorithm implementation, generated artifact and compatibility fixture.
5. Run license and notice checks before adding a component; record SPDX identifiers, copyright notices, license texts and required attributions.
6. Do not assume an API name, binary, JAR, source archive or Oracle download is open source merely because it is available.
7. Do not use Java/Oracle/OpenJDK trademarks in a way that suggests affiliation, endorsement or compatibility certification.
8. If any implementation must reuse or derive from licensed upstream code, stop the clean-room path and conduct an explicit license/compatibility review before merging it.

The EU Software Directive distinguishes protected program expression from underlying ideas and principles, but that is not a blanket permission to copy implementations, documentation or other protected material. This document is an engineering policy, not legal advice; material licensing decisions require a qualified review.

References:
- [OpenJDK licensing information](https://openjdk.org/legal/)
- [Oracle Java licensing FAQ](https://www.oracle.com/java/technologies/javase/jdk-faqs.html)
- [Directive 2009/24/EC, Article 1](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32009L0024)
- [U.S. Copyright Office Circular 33](https://www.copyright.gov/circs/)

## 7. Implementation sequence and gates

Implement small, reviewable slices. Do not launch a rewrite of the whole runtime or merge a feature because a catalogue row exists.

### Phase 0 — inventory and contracts

- Produce a Java capability inventory with one row per capability, source/version, status, Reaper owner, target profile, dependencies, risk and acceptance test.
- Mark every item `adopt`, `adapt`, `optional`, `defer` or `reject`; record the reason.
- Reconcile the matrix with `docs/POLYGLOT_CAPABILITY_LAYER.md`, `docs/FEATURES.md`, `language/features.json` and the current native/compiler contracts.
- Define package, type, task, memory, FFI and diagnostic contracts before code.
- Establish a license/provenance ledger and dependency policy.

**Gate:** no unexplained conflict between the roadmap, feature registry, compiler and runtime semantics.

### Phase 1 — type-system foundation

- Complete source-level type declarations, typed functions and stable diagnostics.
- Add records/enums, generics and constraints, traits/interfaces and pattern matching in separate increments.
- Define null/absence and errors using Reaper-owned `Option`/`Result` semantics.
- Add canonical IR support and golden HIR/MIR/LIR plus Span fixtures.

**Gate:** valid and invalid fixtures are tested; existing `.rpr` programs retain their established behavior.

### Phase 2 — memory and ABI safety

- Complete ownership/borrowing/regions and deterministic cleanup.
- Define allocator profiles, `no_alloc` checks and stack/resource budgets.
- Version the native ABI and validate layout, alignment, ownership and error propagation.
- Extend host FFI only through explicit capability grants.

**Gate:** negative tests prove that forbidden allocation, lifetime escape, ABI mismatch and unauthorized FFI fail deterministically.

### Phase 3 — concurrency

- Add structured task scopes, cancellation, deadlines and typed task results.
- Add bounded lightweight task scheduling and backpressure.
- Add scoped context, channels and synchronization primitives.
- Add deterministic scheduler tests and concurrency stress tests.

**Gate:** cancellation, failure, timeout, leak and race tests pass; limits are measurable.

### Phase 4 — standard library and platform adapters

- Expand collections, text/Unicode, time, filesystem, networking, security and serialization through separately versioned modules.
- Start from host-independent contracts, then add OS adapters.
- Add HTTP/2 and HTTP/3 only through vetted implementations and target capability checks.
- Add embedded/kernel-safe subsets without pulling in the managed application runtime.

**Gate:** API, behavior, resource and security tests pass per supported target.

### Phase 5 — native compilation and performance

- Expand typed lowering through HIR/MIR/LIR, verified VM bytecode and native backends.
- Add optimization passes one at a time with differential correctness tests.
- Introduce profile-guided optimization and AOT cache only with reproducibility/invalidation tests.
- Benchmark startup, throughput, tail latency, memory, binary size and code-size regressions.

**Gate:** the reference runtime, VM and native output agree on the declared conformance suite; performance claims include reproducible measurements.

### Phase 6 — tooling and package ecosystem

- Complete LSP/DAP workflows, formatter, linter, doc generator, REPL, profiler and recorder.
- Add offline package resolution, lockfiles, signing, SBOM and vulnerability/license checks.
- Add minimal deployable runtime images and transactional upgrades.

**Gate:** clean offline builds, deterministic dependency graphs, diagnosable package failures and install/rollback tests.

### Phase 7 — Dak OS integration

- Publish stable contracts for Dak services, process/task management, memory, filesystem, networking and security.
- Integrate one adapter at a time with Dak OS and the relevant repositories.
- Keep kernel/firmware profiles deterministic and allocation-bounded.
- Qualify privileged paths only on supported hardware or an explicitly identified emulator/simulator.

**Gate:** cross-repository contract tests and target evidence exist. A mocked host test is never described as real hardware validation.

## 8. Required CI and evidence

For each accepted capability, require:

- positive, negative and boundary tests;
- golden AST/typed IR/bytecode or native output where relevant;
- source-map and diagnostic assertions;
- reference-versus-VM-versus-native differential fixtures;
- memory, allocation and task-budget tests;
- ABI layout and compatibility tests;
- deterministic/reproducible build checks;
- fuzz/property tests for parsers, serializers and protocol boundaries;
- benchmark baselines for performance-sensitive changes;
- license, dependency provenance and SBOM checks;
- documentation and feature registry updated in the same change.

Use separate PRs for architecture contracts, language semantics, runtime, native lowering, tooling and OS adapters. Keep `main` protected; require CI and review; use Conventional Commits and squash-merge only after all gates pass.

## 9. Definition of done

The Java capability programme is not complete when Reaper merely looks more like Java. It is complete only when each accepted capability has:

1. an independently authored Reaper design and implementation;
2. documented semantics, versioned contracts and explicit target support;
3. reference-runtime behavior and native/VM behavior where claimed;
4. positive, negative, regression and differential tests;
5. performance/resource/security evidence appropriate to its profile;
6. source mapping, diagnostics and editor/tooling integration;
7. license/provenance records and compatible dependencies;
8. documentation and machine-readable maturity status;
9. an explicit Dak OS integration decision.

The result should be a Reaper-native systems language and development platform that benefits from Java's decades of engineering while remaining smaller where that is an advantage, stricter where systems safety requires it, and independent in source, runtime, ABI and identity.
