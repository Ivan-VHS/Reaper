# REAPER CONSTITUTION
## 666 Rules of Evolution — Ivan-VHS

**Version:** 1.0.0  
**Date:** 2026-11-25  
**Author / maintainer:** Ivan-VHS  
**Scope:** Reaper language, compiler, runtime, toolchain and declared integrations  
**Status:** Normative constitution and engineering direction; implementation maturity remains evidence-based

> Think broadly. Change narrowly. Verify completely.  
> Code has rhythm. Contracts have weight. Nothing ships on metaphor alone.

## 1. Purpose

This Constitution turns the 666 principles for Reaper into a reviewable framework spanning language identity, syntax, systems programming, tooling, authorial craft, ethics, ecosystem integration, performance/security profiles and governance.

The number **666** is an organizing identity. It does not mean every rule is compiler-enforced or implemented today. Rules have different scopes and authority.

## 2. Rule classes

| Class | Meaning | Application |
|---|---|---|
| CORE | Семантические инварианты | RFC, language specification и conformance tests |
| STYLE | Читаемость и code craft | Formatter, linter и review |
| TARGET | Аппаратные и платформенные требования | Только на названной архитектуре/ABI/OS |
| ROADMAP | Будущие возможности | Planned до реализации и проверки |
| CRAFT | Музыкальные метафоры | Человеческие review prompts, не compiler errors |
| CULTURE | Этика и сообщество | Прозрачная практика и человеческое управление |
| ECOSYSTEM | Интеграции и deployment | Versioned adapters, owner и threat model |
| PROFILE | Performance/security профили | Измеримый budget на конкретном target |
| GOVERNANCE | Процесс изменения Конституции | RFC, release policy и GitHub governance |

## 3. Authority order

When rules conflict, apply this order:

1. Memory safety, security, correctness and data integrity.
2. Language specification, ABI and external protocol requirements.
3. Compatibility and versioned public contracts.
4. Target profile and measured performance constraints.
5. Repository-local style and formatter.
6. Aesthetic preference and metaphor.

A lower item cannot override a higher one. No rule authorizes unsafe code, privileged access, hidden network activity or breaking compatibility without review.

## 4. Current implementation boundary

This Constitution does not change what Reaper can parse or execute today.

- The canonical source surface uses `craft`, `make`, `vary`, `change`, `yield`, `emit` and composition with `::`.
- The Python reference runtime remains the broad compatibility implementation.
- The native C17 path is a partial compiler track, not full language parity or a direct freestanding ELF backend.
- Reaper-written bootstrap components are partial; Reaper is not yet self-hosting.
- The hardware MMIO API is a checked descriptor/callback contract; it does not map physical memory or execute privileged device operations.
- Freestanding, no_std, borrow checking, Send/Sync, inline assembly, full async runtime, JIT and direct ELF/PE emitters are not implied by this document.

A capability is available only when source, tests, CI and documentation prove the declared behavior.

## 5. Adoption policy

Do not force all 666 rules into every module. Apply only the rules relevant to a change. Cite rule numbers in RFCs/PRs when they materially affect the decision. A rule number is not a substitute for a requirement, test or engineering justification.

## 6. Nine books
### I. ФИЛОСОФИЯ И ДУХ ЯЗЫКА — Rules 1–74

*Scope: Идентичность, семантика и долгосрочное направление языка. Будущие возможности не считаются текущими реализациями.*

1. Reaper exists to create systems, not merely scripts.
2. Code must be readable by people and deterministic for machines.
3. Every observable behavior needs explainable semantics and a testable contract.
4. Authorial expression matters but never overrides correctness or safety.
5. The language should reduce boilerplate through clear composition.
6. Diagnostics should help locate and repair defects.
7. Dangerous operations stay inside explicit, reviewable boundaries.
8. Language evolution follows real use cases, not fashion.
9. Respect C/C++ heritage without copying their weaknesses.
10. Syntax must express semantics rather than decorative brevity.
11. Keep the language core small and composable.
12. Low-level freedom must coexist with safe high-level APIs.
13. Metaprogramming must be controlled and reproducible.
14. Documentation and tests ship with language features.
15. Use semantic versioning and explicit breaking-change policy.
16. Prefer expressive, clear programs over code golf.
17. A consistent vocabulary is more valuable than novelty.
18. DSLs require grammar, typing and explicit boundaries.
19. Compiler infrastructure should gradually become implementable in Reaper.
20. Abstractions must not add hidden costs without reason.
21. Memory has an owner, lifetime and measurable cost.
22. Concurrency requires a defined synchronization and memory model.
23. DuckOS is a target direction, not a claim of readiness.
24. C interoperability uses versioned ABI and explicit unsafe boundaries.
25. Compile-time evaluation is bounded and reproducible.
26. Typing is strict; inference never guesses unknown semantics.
27. Pattern matching must check state handling.
28. Result/Option are preferred for expected failure and absence.
29. Exceptions must not hide ordinary control flow.
30. Hardware APIs must be typed and validated.
31. Modules follow responsibility boundaries, not file-count dogma.
32. Resource cleanup is deterministic where the target permits.
33. Generics should avoid unnecessary runtime overhead.
34. Async defines cancellation, ownership and error propagation.
35. Hardware registers may have typed target-specific contracts.
36. Macros must prevent accidental name capture.
37. Comptime has explicit step, memory and access limits.
38. Test blocks belong only in test builds.
39. Fuzz/property testing belongs in the language quality loop.
40. Refactoring preserves behavior and supports safe symbol rename.
41. Hot reload is limited to profiles with safe state replacement.
42. ABI stability is defined per major version and target.
43. Formatting tools support style without changing semantics.
44. Unicode identifiers need normalization; ASCII remains preferred in system APIs.
45. The language must be learnable and scalable in expressive power.
46. Development uses transparent RFCs and evidence.
47. Licensing and patent terms must be legally precise.
48. Formats must support archival and reproducible builds.
49. Compatibility remains until its cost threatens safety or evolution.
50. Deprecation periods depend on risk and ecosystem reach.
51. Critical paths should support formal verification.
52. The type system prevents classes of errors it can actually prove.
53. Legacy interoperability uses explicit adapters.
54. Inline assembly requires target constraints and operand checks.
55. Linker scripts/layout files are versioned and validated.
56. Custom allocators define alignment, failure and release contracts.
57. Slices/views are distinct from ownership and raw pointers.
58. Encoding is explicit; UTF-8 is the primary text format.
59. Core operations must not allocate invisibly without documentation.
60. Copy, move and borrow semantics are explicit.
61. Borrow diagnostics are local and explainable.
62. Lifetime inference is allowed only when safety can be proven.
63. Polymorphism supports composition without mandatory inheritance.
64. Prefer composition over inheritance for reuse.
65. Traits use static dispatch by default where appropriate.
66. Dynamic dispatch is explicit and has visible costs.
67. Associated types clarify trait contracts.
68. Where constraints remain readable and locally checkable.
69. Const generics validate ranges and ABI limits.
70. Variadic generics require clear semantics and real use cases.
71. Higher-kinded abstractions remain a roadmap option, not a core obligation.
72. The language specification is the source of truth.
73. Public language features require conformance and negative fixtures.
74. Compiler stages expose inspectable IR and source-map artifacts.

### II. СИНТАКСИС И ЧИТАЕМОСТЬ — Rules 75–148

*Scope: Стиль и кандидаты синтаксиса. Для текущего Reaper применяются только реально поддерживаемые конструкции.*

75. Formatting is deterministic and checked by a formatter.
76. Control-flow blocks have unambiguous visual boundaries.
77. Statement terminators are defined by grammar, not borrowed from C by habit.
78. Trailing commas are used where grammar and diffs benefit.
79. Local variable names follow the language convention.
80. Type names follow the language convention.
81. Constants follow the repository convention.
82. Functions name the action and its subject.
83. Access control is semantic; underscores are not access control.
84. Public APIs document contracts, examples and errors.
85. Comments explain reasons and invariants, not obvious operations.
86. Line length is a formatter/review concern, not a universal hard law.
87. Deep nesting triggers review, not automatic failure.
88. Split long functions when sub-responsibilities are real.
89. Parameter count is judged by cohesion, not an arbitrary number.
90. Public functions expose a clear result and error contract.
91. Public type annotations are required where the compiler supports them.
92. Wildcard imports must not obscure symbol origin in public/system code.
93. Aliases are allowed for clarity and conflict resolution.
94. Module paths must be predictable.
95. Long chains are split when stages become hard to inspect.
96. Brackets and blocks follow one formatter.
97. Blank lines separate meaning, not every statement.
98. Manual vertical alignment must not create diff noise.
99. Boolean arguments need meaningful names or typed options.
100. Magic numbers become named constants when meaning is not obvious.
101. Raw strings are used when they improve literal accuracy.
102. Regexes are precompiled when supported and worthwhile.
103. Comments capture WHY and constraints.
104. TODO/FIXME names a concrete issue and completion test.
105. Unused symbols/imports are detected by tools.
106. Shadowing is allowed only when local meaning remains clear.
107. Mutability is explicit; immutable bindings are preferred.
108. Global mutable state is restricted and owned.
109. Short expression functions are fine when readable.
110. Early return separates invalid states from the main path.
111. Guard clauses appear early unless they obscure cleanup.
112. Match branches follow formatter and grammar.
113. Enum variants have distinct stable semantic names.
114. Struct fields follow language and domain conventions.
115. Tuple structs are for small obvious values.
116. Unit types are markers only when meaningful.
117. Newtypes distinguish units, IDs and constrained values.
118. Operator overloading follows natural algebraic meaning only.
119. Deref/coercion must not hide ownership or allocation.
120. Implicit conversions are forbidden at ABI/security boundaries.
121. Panic output is distinct from normal output.
122. Format strings are checked statically when supported.
123. Raw identifiers serve FFI and reserved-word compatibility.
124. Lifetime names are short when simple and descriptive when complex.
125. Self-describing names beat redundant comments.
126. Use common abbreviations such as idx, len, buf, src and dst.
127. Avoid Hungarian notation when types are in signatures.
128. Interface names describe role, not mandatory I-prefixes.
129. Factories use new/create/build or a domain verb.
130. Conversion APIs distinguish borrowed, owned and consuming conversion.
131. Predicates use is_/has_/can_ according to meaning.
132. Iterator laziness and materialization are documented.
133. Collectors make allocation and ownership visible.
134. Closure capture follows visible language rules.
135. Async and sync operations are distinguishable in APIs.
136. Await and cancellation are explicit.
137. Task spawning exposes ownership, priority and cancellation.
138. Error propagation has unambiguous conversion rules.
139. unwrap/expect belong in tests or proven-impossible states.
140. Map/filter chains must not hide cost or side effects.
141. Indexed loops are valid when position and access control matter.
142. Infinite loops have an explicit exit or documented OS/embedded role.
143. Labeled break/continue are rare and readable.
144. Goto is not introduced into safe high-level code.
145. Macros/codegen are visibly distinct from ordinary calls.
146. Attributes are grouped by role and documented.
147. Derive/codegen behavior is explicit and reproducible.
148. Эстетика не оправдывает неоднозначный control flow.

### III. СИСТЕМНОЕ ПРОГРАММИРОВАНИЕ И ПАМЯТЬ — Rules 149–222

*Scope: Системный профиль. Правила действуют лишь там, где это поддерживают язык, ABI и target.*

149. Pointer arithmetic requires unsafe or a proven equivalent boundary.
150. Nullability uses a distinct type when the type system supports it.
151. Dangling references are prevented by lifetimes or isolated unsafe contracts.
152. Ownership prevents double-free where the implementation can prove it.
153. Data races require synchronization and a defined memory model.
154. Stack overflow has a detection policy or documented limit.
155. Allocator APIs support arena, pool, slab and general allocation profiles.
156. SIMD provides portable fallbacks and equivalence tests.
157. Bit operations define width and shift behavior.
158. Endianness is explicit at binary/device boundaries.
159. Alignment follows type layout or is checked at runtime/FFI boundaries.
160. Padding/layout follows documented repr and ABI contracts.
161. Volatile is for observable device access, not a replacement for atomics.
162. Memory barriers have defined architecture and language guarantees.
163. Atomics define ordering and synchronization scope.
164. Thread-local storage has a clear lifecycle.
165. Signal handling is platform-specific and makes no false safety claims.
166. Interrupt handlers have bounded time, allocation and locking behavior.
167. DMA buffers define pinning, direction, cache sync and ownership.
168. MMIO mapping is supplied by a trusted driver/platform adapter.
169. Register banks define width, offset, access, endian and side effects.
170. Boot handoff is a versioned ABI with validated structures.
171. ELF/PE parsing bounds every size, offset and type.
172. Symbol resolution separates link-time and runtime policy.
173. Dynamic loading requires permission, ABI compatibility and trust checks.
174. Plugin ABI is versioned and has lifecycle/isolation rules.
175. Serialization preserves schema version, bounds and provenance.
176. Network I/O provides backpressure, cancellation and bounded buffers.
177. File paths have safe handles and canonicalization at the API boundary.
178. Permissions use capability/ACL contracts, not string assertions.
179. Cryptography uses reviewed primitives and explicit parameters.
180. Randomness distinguishes CSPRNG from reproducible test sources.
181. Monotonic and wall clocks have distinct semantics.
182. Duration/Instant avoid overflow and invalid comparisons.
183. Deterministic floating point is an explicit profile.
184. Fixed point supports embedded/numeric use with declared precision.
185. Arbitrary precision decimal remains optional.
186. Matrix/vector optimizations are checked against scalar references.
187. Graph algorithms define adjacency and ownership contracts.
188. Parsing combinators support bounds and source spans.
189. Logging is structured and cheap when disabled.
190. Tracing uses safe IDs and context.
191. Profiling must not change semantics.
192. Benchmarks record target, inputs, flags and method.
193. Coverage distinguishes line/branch and is not a quality score.
194. Sanitizers run on supported host/native targets.
195. Valgrind-like tools are used where compatible.
196. Cross-compilation defines triple, ABI, CPU features and sysroot.
197. Tier targets have a published test matrix.
198. Custom targets use versioned schemas, not compiler forks.
199. Linker plugins need a trust and reproducibility model.
200. ThinLTO is an optimization profile, not a universal default.
201. FatLTO is used when measured benefit justifies build cost.
202. PGO records profile provenance and binary identity.
203. Post-link optimization compares behavior, size and speed.
204. Backends are interchangeable only when IR semantics are preserved.
205. Interpreter/VM supports interactive and compatibility execution.
206. JIT is optional application runtime, never a boot prerequisite.
207. AOT is the primary direction for systems/freestanding targets.
208. Wasm/WASI has its own ABI and capability model.
209. GPU compute uses versioned shader/SPIR-V interfaces.
210. FPGA/ASIC remains a research backend.
211. Real-time profiles define latency budgets and platform assumptions.
212. WCET applies only to a named compiler, target and environment.
213. Power profiling uses real measurements and states error margins.
214. Thermal APIs do not assume uniform sensor availability.
215. Battery status is a platform capability.
216. Sensors/actuators use typed driver interfaces.
217. Robotics APIs are specialized libraries over system types.
218. Control primitives document units, stability and numeric bounds.
219. DSP has a reference implementation and measured optimized paths.
220. Audio APIs define sample format, clock, latency and buffer ownership.
221. Video/framebuffer APIs define stride, format, lifetime and synchronization.
222. Физические и виртуальные адреса не смешиваются в одном контракте.

### IV. ЭКОСИСТЕМА И ИНСТРУМЕНТЫ — Rules 223–296

*Scope: Целевой developer experience. Запись правила не доказывает наличие команды или интеграции.*

223. Package manager uses versioned manifests.
224. Registries may federate, but source resolution is explicit.
225. Dependencies are locked for reproducible builds.
226. Semantic versioning is checked against public contracts.
227. Yanking prevents new resolution without breaking existing lockfiles.
228. Private registries enforce least privilege and secure authentication.
229. Workspace support defines shared dependencies and test boundaries.
230. Feature flags document API and binary effects.
231. Development dependencies are separate from production.
232. Build scripts run with bounded privileges and reproducible inputs.
233. Artifact caches key compiler, target, flags and all inputs.
234. Remote execution verifies build inputs and artifact identity.
235. Hermetic builds minimize ambient host state.
236. Reproducible builds target bit-identical output in a pinned environment.
237. SBOMs include artifact provenance.
238. Vulnerability scanning does not replace review.
239. License checks analyze real dependencies and license terms.
240. reaper fmt is deterministic and idempotent.
241. reaper lint has severity settings and stable diagnostic codes.
242. Semantic lints detect defects, not personal taste.
243. reaper doc links APIs, contracts, examples and limitations.
244. Documentation examples run on the declared toolchain.
245. Benchmarks publish methodology and inputs.
246. REPL history/completion does not alter batch semantics.
247. Debugger support matches documented ABI and symbols.
248. LSP remains the editor integration protocol.
249. DAP exposes only implemented debugger states.
250. Syntax highlighting follows the grammar.
251. Snippets are syntax-checked and do not advertise unsupported features.
252. Refactoring tools respect scope and source maps.
253. Migration tools preview diffs before changing files.
254. Fuzzers bound time, memory and input size.
255. Property tests record seeds and minimize failures.
256. Mocks must not replace critical ABI/device contract tests.
257. Integration harnesses run dependencies only by explicit profile.
258. E2E tests distinguish host, browser and device environments.
259. Performance gates use stable measurement environments.
260. Binary-size gates define target, linker flags and baseline.
261. Dependency graphs show provenance and versions.
262. Call graphs distinguish static/dynamic calls.
263. Type dependency analysis finds unwanted coupling.
264. Dead-code reports distinguish public ABI and conditional compilation.
265. Binary explorers link symbols/sections to available source metadata.
266. Startup profilers name the measured phase and target.
267. Memory trackers report method and limitations.
268. CPU flamegraphs use valid sampling data.
269. I/O latency charts state timestamps and units.
270. Network tracing is off by default and never silently exports data.
271. Log analysis preserves provenance and process separation.
272. Metrics exporters require opt-in and respect local data policy.
273. Tracing exporters use explicit endpoints and network capability.
274. Alerts have rate limits and safe notification policy.
275. Dashboard-as-code is an optional infrastructure integration.
276. Infrastructure DSL is a domain package, not a language prerequisite.
277. Configuration has schema, defaults, bounds and migration.
278. Secrets enter through protected runtime channels, not source literals.
279. Environment management reads only declared sources.
280. Container generation is tooling, not a language dependency.
281. Kubernetes manifests require a real deployment target.
282. Serverless deployment uses explicit provider adapters and tests.
283. Edge/Wasm deployment has bounded ABI and capabilities.
284. Mobile targets need a confirmed ABI/SDK matrix.
285. Desktop framework choices do not define language semantics.
286. Web/Wasm support requires a backend and runtime tests.
287. Embedded profiles define startup, memory map, allocator and panic policy.
288. Kernel profiles exclude hosted runtime dependencies.
289. Boot templates match selected firmware protocol and ABI.
290. Driver frameworks preserve privilege separation and device ownership.
291. Filesystem drivers define crash, flush and error semantics.
292. Network stacks are explicit libraries/services, not hidden effects.
293. Graphics bindings separate platform APIs from rendering abstractions.
294. Audio bindings describe actual host APIs and do not promise universal latency.
295. Input bindings preserve device metadata while normalizing events.
296. Windowing adapters have a platform support matrix.

### V. МУЗЫКАЛЬНОСТЬ И РИТМ КОДА — Rules 297–370

*Scope: Авторская эстетика Ivan-VHS. Музыкальные метафоры направляют композицию, но не становятся автоматическими lint errors.*

297. Code has a reading rhythm: dense and simple blocks alternate to help understanding.
298. Drop is the algorithmic climax, not a reason to compress statements.
299. Intro prepares only the necessary context.
300. Verse is the main execution story.
301. Chorus is repeated behavior extracted into a tested shared function.
302. Bridge is an explicit state/data transition.
303. Outro releases resources and returns control cleanly.
304. Blank lines are pauses between semantic blocks.
305. Syncopation is allowed when execution order remains clear.
306. Groove means frictionless reading, not forced stylistic tricks.
307. Layering keeps abstraction levels separate.
308. Sampling reuses ideas only with license/provenance review.
309. Remixing creates a distinct solution, not copied implementation.
310. Distortion is a metaphor for a localized unsafe/low-level boundary.
311. Reverb is the context supplied by docs, source maps, tests and decisions.
312. Delay reminds us to handle async consequences, cancellation and timeouts.
313. Filter removes unnecessary complexity without loss of semantics.
314. EQ balances safety, control, performance and readability.
315. Compression is allowed only if it hides neither control flow nor cost.
316. Limiter represents explicit budgets for size, time, memory and retries.
317. Sidechain represents dependencies that constrain another action.
318. Automation changes behavior through explicit configuration and validated state.
319. Modulation is controlled variation through types, parameters and traits.
320. Resonance means a solution fits the real problem.
321. Dissonance is useful in negative tests for incompatible states.
322. Resolution explicitly and verifiably settles conflicts.
323. Tempo means algorithmic complexity fits workload.
324. Time signature is the organization of semantic blocks.
325. Key signature is the stable type/API vocabulary.
326. Dynamics express importance through interfaces, errors and docs.
327. Articulation means precise operations, types and boundaries.
328. Phrasing means each logical unit has a clear result.
329. Motif is a domain invariant shared across modules.
330. Variation evolves a pattern without blind copy/paste.
331. Development deepens a solution while preserving intent.
332. Recapitulation returns to the initial requirement for verification.
333. Coda summarizes the result and known limits.
334. Improvisation is acceptable in prototypes when hypotheses are labeled.
335. Jam session is respectful review of alternatives.
336. Solo means a clear module owner.
337. Ensemble means modules cooperate through contracts.
338. Conductor coordinates dependencies without becoming a global bottleneck.
339. Score is the specification used by implementers.
340. Recording is a comprehensible Git history.
341. Mastering is release review of quality, signatures and reproducibility.
342. Mixing balances API, performance and resources during integration.
343. Arrangement places components in an understandable structure.
344. Instrumentation selects technology for the actual task.
345. Timbre is Reaper's recognizable clarity, not strange identifiers.
346. Texture makes code density match problem complexity.
347. Harmony is compatibility across types, versions and failures.
348. Counterpoint gives parallel processes independent ownership and synchronization.
349. Fugue repeats a domain invariant while keeping one canonical source.
350. Canon repeats verified patterns without mechanical duplication.
351. Ostinato preserves foundational invariants during refactoring.
352. Pedal point keeps stable ABI beneath internal change.
353. Cadence gives each operation a clear completion.
354. Modulation requires explicit type/state transition.
355. Chromaticism localizes incompatible interfaces in adapters.
356. Diatonicism keeps core constructs simple and predictable.
357. Microtonality is fine tuning with measurable effect.
358. Polyrhythm coordinates independent loops and schedulers by deadline.
359. Polymeter permits different block sizes under explicit contracts.
360. Hemiola requires defined interaction between unsynchronized cycles.
361. Syncopation must not become accidental execution ordering.
362. Swing is measured and bounded timing variation.
363. Shuffle gives repeated work deterministic queue order.
364. Groove quantization lets formatters preserve structural rhythm without manual alignment.
365. Humanize means natural names, errors and examples.
366. Velocity measures operation cost and priority.
367. Aftertouch handles sustained work through cancellation/backpressure.
368. Pitch bend preserves type and numeric range.
369. Vibrato bounds periodic parameter variation.
370. Tremolo requires bounded work and stable order for rapid state changes.

### VI. АВТОРСТВО И ЭТИКА — Rules 371–444

*Scope: Этические и культурные обязательства, требующие человеческой ответственности.*

371. Code authorship and provenance must be transparent.
372. Inspiration does not permit copying protected implementation.
373. Authors, sources and licenses follow applicable terms.
374. Open development respects proprietary constraints and third-party rights.
375. Security tools are built for defense and authorized testing.
376. Privacy by design minimizes collection, storage and transfer.
377. Secure defaults apply where safe behavior is contractually defined.
378. Accessibility matters in APIs, docs, IDE and apps.
379. Community language stays respectful and understandable.
380. Mentorship supports new contributors.
381. Critique targets code behavior and evidence, not people.
382. Planning respects maintainers' health and sustainable pace.
383. Crunch is not a normal release strategy.
384. Decisions document alternatives and consequences.
385. Mistakes are acknowledged and analyzed without blame.
386. Learning is supported by examples, review and documentation.
387. Knowledge is recorded, not kept only in conversation.
388. Different engineering approaches are judged by evidence.
389. Meritocracy is balanced with respect and fair participation.
390. Technology choices consider resources, support and energy.
391. Long-term reliability beats short-lived impression.
392. Legacy code is studied before deletion.
393. Documentation respects the reader's time.
394. Tests protect users and future changes.
395. Review is collaboration toward a better solution.
396. Release earns trust through evidence.
397. Support communicates real limitations and lifecycle.
398. Deprecation warns consumers and provides migration.
399. Removal checks dependencies and compatibility.
400. New features begin with a real need.
401. Refactoring changes structure without accidental behavior changes.
402. Archives preserve history, licenses and checksums.
403. Evolution should improve resilience and understandability.
404. Revolution requires evidence that the old model is insufficient.
405. Tradition remains while it serves quality and compatibility.
406. Innovation is tested with a prototype and success criterion.
407. Simplicity covers requirements without sacrificing guarantees.
408. Necessary complexity is acknowledged and documented.
409. Abstraction hides detail, not ownership, cost or failure.
410. Concrete implementation remains inspectable and testable.
411. Generalization needs more than one real consumer.
412. Specialization needs measured requirements and a clear boundary.
413. Integration uses versioned contracts.
414. Separation protects responsibility and independent verification.
415. Automation reduces repeated work without removing control.
416. Manual control remains for risky or ambiguous operations.
417. Forecasts state assumptions and uncertainty.
418. Failure response has predefined safe states.
419. Prevention is preferred to recovery.
420. Recovery does not hide root cause or data loss.
421. Diagnostics distinguish symptom, cause and blast radius.
422. Forecasts are not presented as facts.
423. Debugging observes behavior without changing semantics.
424. Refactoring proceeds in small, regression-tested steps.
425. Migration preserves data, provenance and compatibility.
426. Dead code removal follows reference checks.
427. Legacy rehabilitation preserves necessary behavior and docs.
428. Postmortems record failure conditions and systemic improvements.
429. Initialization has explicit preconditions and partial states.
430. Project growth updates structure and documentation.
431. Maturity means stable contracts and honest release notes.
432. API aging uses deprecation and migration policy.
433. Completion means postconditions and resource cleanup hold.
434. Major releases include compatibility and migration plans.
435. Open source does not promise eternal maintenance without an owner.
436. Platform limits are part of the engineering contract.
437. Recursion is bounded or has a proven termination condition.
438. Zero differs from absence and uninitialized state.
439. Single responsibility does not imply a global singleton.
440. Multiple components are valid with clear ownership and coordination.
441. Completeness claims are limited to published scope.
442. Potential is not evidence of implementation.
443. Every delivery respects users, their data and their time.
444. Конфликт интересов и происхождение зависимостей раскрываются.

### VII. МУЛЬТИДИСЦИПЛИНАРНОСТЬ И СВЯЗИ — Rules 445–518

*Scope: Экосистемные цели. Конкретные интеграции требуют владельца, контракта и тестов.*

445. DuckOS integration uses typed wrappers over a versioned syscall ABI.
446. Graphics integrates through native compositor APIs and resource ownership.
447. Audio APIs define sample format, latency, clock and buffer lifecycle.
448. I/O treats events as bounded streams with backpressure.
449. Network APIs require explicit capability and no hidden network access.
450. Filesystem APIs use safe path handles and explicit permissions.
451. Processes have address-space isolation and managed lifecycle.
452. Threads and async tasks define stack, cancellation and scheduling.
453. Synchronization is chosen for the use case; lock-free is not a goal by itself.
454. IPC uses typed messages, bounded size and protocol versions.
455. RPC uses an IDL/schema and verifiable wire contract.
456. Serialization starts with schema and compatibility policy.
457. Configuration is typed, validated and migratable.
458. Logging uses structured fields, levels and correlation IDs.
459. Metrics distinguish counters, gauges and histograms with units.
460. Tracing correlates operations through safe context IDs.
461. Profiling states sampling/instrumentation error.
462. Debugging uses introspection APIs with access control.
463. Testing combines unit, property, fuzz, integration and target tests.
464. Documentation examples execute on the declared toolchain.
465. Packaging creates verifiable bundles with manifests and hashes.
466. Deployment uses health gates and atomicity where supported.
467. Rollback is tested for state-changing updates.
468. Monitoring has resource limits and privacy policy.
469. Scaling follows measured limits, not auto-scale slogans.
470. Load balancing considers latency, capacity and fairness.
471. Caching defines ownership, invalidation and consistency.
472. Persistence documents durability, ordering and recovery.
473. Consistency is selected and documented per store.
474. Availability defines permissible degradation and failure behavior.
475. Network partitions define protocol, timeout and conflict policy.
476. Latency measurement includes tail percentiles and methodology.
477. Throughput includes backpressure and queue limits.
478. Resource use is bounded for memory, CPU, handles and I/O.
479. Compute cost is measured on a declared workload profile.
480. Energy use is recorded where valid measurement exists.
481. Bias/fairness checks apply where product decisions and data warrant them.
482. Resource allocation is transparent and testable.
483. System decisions are explainable at the contract level.
484. Privileged actions are attributable and auditable.
485. Data sovereignty preserves local user control.
486. Security uses layers, not one check.
487. Safety defaults deny dangerous action without required authority.
488. Reliability uses defined SLI/SLO when applicable.
489. Maintainability is assessed through change cost and clarity.
490. Plugin points use versioned ABI and trust policy.
491. Composability uses small components and explicit contracts.
492. Polyglot interop uses adapters, not blended memory models.
493. Portability claims apply only to tested targets.
494. Scalability avoids rewrites caused by hidden API limits.
495. Evolvability uses schemas, versions and migrations.
496. Understandability is evaluated through reading tasks and diagnostics.
497. Testability uses explicit seams and injectable adapters.
498. Observability provides useful signals without sensitive data leaks.
499. Controllability provides explicit settings with safe bounds.
500. Predictability aims for deterministic semantics and stable ordering.
501. Adaptability uses configuration and platform profiles.
502. Resilience recovers without hiding data loss.
503. Antifragility is an architectural aspiration, not a measured guarantee.
504. Robustness is tested with malformed, boundary and hostile inputs.
505. Elegance prefers the simplest solution that preserves required guarantees.
506. Beauty is an author value, not an exemption from review.
507. Joy is supported through good tools and low workflow friction.
508. Pride follows real quality, not marketing.
509. Humility labels unknown and unverified behavior.
510. Curiosity uses experimental branches and reproducible prototypes.
511. Courage changes outdated designs with compatibility plans.
512. Patience tests hard hypotheses without indefinite release delay.
513. Perseverance completes chosen scope.
514. Integrity aligns claims, source and behavior.
515. Honesty forbids presenting plans as implementation.
516. Kindness appears in readable code and respectful review.
517. Wisdom includes declining unjustified functionality.
518. Care for craft appears in tests, docs and maintenance.

### VIII. ТЕХНИЧЕСКАЯ ЭКСТРЕМАЛЬНОСТЬ И ГРАНЬ — Rules 519–592

*Scope: Профили производительности и безопасности. Требуют target, threat model, budget и evidence.*

519. GC pause budgets apply only to a GC profile and named target.
520. Hot paths avoid allocation when workload and budget justify it.
521. Cache-line alignment targets measured false sharing.
522. Branch hints require measured benefit and safe fallback.
523. Prefetch is target-specific and profile-driven.
524. Vectorization reports target selected critical loops.
525. Inlining decisions are inspectable, not manually forced everywhere.
526. Register allocation is examined with backend diagnostics/disassembly.
527. Instruction scheduling is target-specific and benchmarked.
528. Pipeline stalls use hardware counters where available.
529. TLB misses are profiled on named architecture.
530. Page faults are classified by cause and context.
531. Context switches are measured for scheduler analysis.
532. Syscall overhead is measured on target environment.
533. Lock contention is profiled before redesign.
534. Memory bandwidth optimization follows real access patterns.
535. CPU affinity is explicit when latency/NUMA needs it.
536. NUMA allocation respects topology and remote-access cost.
537. Huge pages require platform support and measured benefit.
538. Transparent huge pages follow OS policy when available.
539. Swap policy belongs to a system profile, not language semantics.
540. OOM policy defines failure and recovery behavior.
541. Cgroups limits use a Linux adapter.
542. Namespaces isolate processes where the OS supports them.
543. Seccomp filters match a tested syscall profile.
544. AppArmor/SELinux profiles are OS integrations.
545. Capabilities are minimal and revocable.
546. Chroot/jail is platform protection, not universal sandbox proof.
547. ASLR is enabled and checked on supported target binaries.
548. DEP/NX follows ABI and hardware support.
549. Stack canaries follow build profile and runtime constraints.
550. CFG applies on supported Windows targets.
551. CFI requires compiler/linker/runtime agreement.
552. Shadow stack requires hardware and OS support.
553. Memory tagging is target-specific.
554. Pointer authentication applies only on supported ARM targets.
555. Encryption at rest belongs to storage/key management.
556. Encryption in transit belongs to network protocol profiles.
557. Key rotation has compatibility and recovery plans.
558. Certificate pinning has a trust-root update model.
559. HSM support is an explicit external capability.
560. TPM may protect keys; it is not mandatory for every secret.
561. Secure Boot requires a complete trusted chain and recovery process.
562. Measured boot records protected provenance.
563. Remote attestation requires a threat model and privacy controls.
564. Firmware updates are signed and recoverable.
565. Driver signing is checked before code load.
566. Kernel-module locking follows kernel release policy.
567. Rootkit detection requires a concrete sensor and threat model.
568. Anomaly detection defines baseline and false-positive budget.
569. Behavior analysis collects no more than declared scope.
570. Threat-intelligence ingestion is opt-in and network-explicit.
571. Incident response automation is policy-limited.
572. Forensics preserves provenance and chain of custody.
573. Audit trails define integrity and retention.
574. Compliance reports follow an applicable standard.
575. Policy-as-code is reviewed and tested before deployment.
576. Configuration drift compares against desired state.
577. Configuration is validated before application.
578. Secret scanning runs in local/CI review where supported.
579. License scanning checks real dependencies and provenance.
580. Dependency scanning considers version, source and CVE applicability.
581. Image scanning bounds parsing and never executes inspected payload.
582. Runtime protection has a real enforcement point.
583. Network policy is enforced at a supported runtime/OS boundary.
584. Service mesh is optional infrastructure, not Reaper core.
585. API gateways use typed, versioned contracts.
586. Rate limiting considers fairness, burst and retries.
587. Circuit breakers define open/half-open/closed transitions.
588. Retry budgets prevent cascading retries.
589. Timeout hierarchy coordinates parent/child deadlines.
590. Deadline propagation uses monotonic time.
591. Cancellation is cooperative and releases resources by contract.
592. Cleanup runs on every defined exit/failure path.

### IX. МЕТА-ПРАВИЛА И САМОЭВОЛЮЦИЯ — Rules 593–666

*Scope: Управление Конституцией и экосистемой через прозрачные процессы.*

593. The Constitution is a living versioned document.
594. Normative amendments require RFC.
595. RFCs state motivation, alternatives, impact and migration.
596. Discussion is open within safety and privacy limits.
597. Decisions follow evidence, responsibility and transparent reasoning.
598. Veto powers are limited by published governance.
599. Every rule is periodically reviewed for relevance.
600. Review cycle does not create automatic breaking changes.
601. Deprecation process documents replacement and timing.
602. Migration path is required for incompatible public contracts.
603. Tooling updates with language and format changes.
604. Documentation updates with implementation changes.
605. Users receive timely change notices.
606. Feedback channel has an owner and handling policy.
607. Bug reports include minimal reproduction and environment.
608. Feature requests state use case and success criteria.
609. Questions should not require private implementation knowledge.
610. Discussions have a clear subject.
611. Proposals receive stable ID and status.
612. Decision records preserve context and result.
613. ADRs document major architecture choices.
614. Meeting notes are published when they affect decisions.
615. Roadmap shows dependencies, risks and maturity boundaries.
616. Progress separates delivered, partial and planned.
617. Blockers name owner and removal condition.
618. Risks are reviewed before ABI/format/security-boundary changes.
619. Opportunities are explored in bounded prototypes.
620. Lessons learned become concrete process improvements.
621. Best practices include examples and applicability limits.
622. Anti-patterns describe problem and safer alternative.
623. Gotchas record limitations and workarounds.
624. FAQ does not replace normative specification.
625. Glossary stores canonical terms and translations.
626. Index supports search across versions and subsystems.
627. Cross-references are checked when paths/names change.
628. Link checks avoid secret or unauthorized resources.
629. Examples are tested on declared compiler/runtime profiles.
630. Snippets state language, version and compile status.
631. Diagrams are versioned with architecture decisions.
632. Videos include captions when used as documentation.
633. Podcasts/oral material receive written summaries when published.
634. Articles retain date, author and source links.
635. Social posts are not sources of truth for contracts.
636. Community channels define retention and privacy.
637. Issues are triaged by type, priority and owner.
638. Pull requests use review and protected CI checks.
639. Commit signing follows protected-branch/key policy.
640. Release tags are annotated/signed where supported.
641. Release notes list material changes and limitations.
642. Changelog is human-readable and version-linked.
643. Breaking changes are highlighted with migration notes.
644. New features include a minimal runnable example.
645. Bug fixes identify behavior and regression test.
646. Performance claims include measurements and methodology.
647. Security patches follow coordinated disclosure.
648. Deprecations state replacement, timing and effects.
649. Removals are justified and include migration guidance.
650. Additions explain motivation and maintenance cost.
651. Changes record differences from previous contracts.
652. Motivation is distinct from technical guarantee.
653. Context links specification and decision.
654. Links point to a specific document version or source path.
655. Authors are credited by actual contribution and license.
656. Reviewers are thanked for useful feedback.
657. Testers/maintainers are credited for verified work.
658. Users provide scenarios and feedback.
659. Contributors receive clear participation and attribution rules.
660. Maintainers rotate knowledge to reduce bus factor.
661. Leaders are accountable for transparent decisions.
662. Participants can challenge decisions without artificial hierarchy.
663. Vision is concise and tied to a verifiable roadmap.
664. Mission limits scope and prevents uncontrolled expansion.
665. Values appear in actual decisions and reviews.
666. Culture is shaped by behavior, not slogans.


## 7. Change control

1. CORE amendments require motivation, alternatives, compatibility impact, migration and conformance tests.
2. STYLE changes explain their benefit and do not conflict with the formatter.
3. TARGET/PROFILE rules name architecture, ABI, firmware/OS, trust assumptions and measurable evidence.
4. ROADMAP/ECOSYSTEM rules identify owner, dependencies, scope and acceptance tests.
5. CRAFT rules never reject correct idiomatic code by themselves.
6. CULTURE/GOVERNANCE changes respect contributor rights, safety and transparent process.
7. Renumbering/removal requires migration notes; numbering remains stable across minor revisions.
8. Amendments update the documentation index, local standards and validators where enforcement changes.

## 8. Review checklist

- [ ] The change serves a stated need.
- [ ] The syntax is supported by the declared compiler/runtime.
- [ ] Ownership, effects, failures and resource bounds are explicit.
- [ ] Target, ABI, privilege and compatibility assumptions are named.
- [ ] Success, failure and boundary tests exist.
- [ ] Performance/security claims are measured or marked as goals.
- [ ] Docs and maturity claims match source and CI.
- [ ] The diff is focused and understandable to a future maintainer.

## 9. Final principle

The Constitution protects Reaper's identity; it does not imprison the language in arbitrary limits. Preserve semantic precision, make the main path readable, expose dangerous boundaries, respect the target and prove behavior independently.

**Think broadly. Build in complete slices. Keep the groove; prove the behavior.**
