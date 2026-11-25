# Reaper Selfhost Migration and Repository Audit Standard

**Document ID:** REAPER-SELFHOST-AUDIT-001  
**Version:** 1.0  
**Status:** Normative migration and safety gates; native audit/rewrite tooling planned  
**Source basis:** OS(2).txt, repository-polishing proposal and selfhost/Python migration proposal  
**Related:** FILE_FORMATS_AND_EXTENSIONS_V1.md, DEFENSIVE_SECURITY_DOCTRINE.md, UNIFIED_DOCUMENTATION_STANDARD.md, quality-repeatability-native.v1.json, improvement-conflict.v1.json

## 1. Purpose

This standard turns the supplied repository-polishing, low-level stream-buffer and self-host migration proposals into a safe, measurable engineering plan.

The source is useful as a direction: contract-first evolution, deterministic repository inspection, ergonomic diagnostics, bounded stream processing, staged self-host rewrites and rollback. Its example implementations are not production-ready and are not copied verbatim.

A source example is not an implementation. A tool is not implemented because its proposed filename appears in a design. Reaper native support is verified only when grammar, compiler/runtime integration, tests and CI prove it.

## 2. Migration policy: remove duplicated responsibility, not languages by slogan

Reaper should become the native source of truth for its language semantics, canonical IR, compiler passes, system contracts and DuckOS-owned system components. Migration must follow semantic parity, not filename extension.

Classify each existing program before changing it:

| Class | Examples | Policy |
|---|---|---|
| Native Reaper core | Lexer/parser, typed IR, optimizer, bytecode VM, native backends, ABI checks | Reaper is the target implementation; maintain a narrow bootstrap path until self-hosting is proven |
| DuckOS-owned system components | Kernel-facing services, process/capability policy, IPC, storage contracts, BAV service logic | New implementations and examples use Reaper; privileged enforcement still requires native DuckOS services |
| Host tooling and CI adapters | Repository discovery, GitHub Actions glue, platform packaging and release scripts | Keep the minimum host adapter needed to bootstrap and operate CI; move domain rules into versioned Reaper contracts |
| Tests and compatibility harnesses | Golden fixtures, ABI tests, differential compiler tests, platform harnesses | Keep the runner that current CI can execute until a native Reaper test runner has parity; do not remove tests to meet a language-purity target |
| Generated, vendored and third-party code | Generated bindings, external toolchains, licensed sources | Do not rewrite automatically; preserve provenance, licences and reproducible generation |

No bulk deletion of Python or other host tooling is allowed. Retire a host tool only after its supported workflows, exit codes, reports, diagnostics, failure behavior and reproducibility are covered by the native replacement. Reaper-owned system semantics must not become permanently dependent on a second, drifting implementation.

## 3. Repository audit service requirements

The proposed reaper_polisher_suite.py describes repository inventory, JSON-contract inspection, source heuristics, metrics, conflict reporting, Markdown/JSON output and whitespace normalization. The shown implementation is not a safe general-purpose patcher and does not generate the semantic code patches claimed in its introduction.

A future audit service MUST separate collection, analysis, reporting and mutation into distinct capabilities.

### 3.1 Collection

- Default to read-only inspection. No source file, configuration or working-tree state may change during audit.
- Establish and report the repository root and snapshot identity. Prefer the tracked index/commit view for CI audits; report untracked files separately.
- Sort paths and directory entries deterministically. Make ignore rules explicit and versioned.
- Reject paths escaping the repository root. Do not follow directory symlinks; inspect file symlinks as link metadata or skip them by explicit policy. Never read or rewrite a symlink target outside the root.
- Apply configurable per-file and total-byte budgets. Oversized files are reported as skipped/incomplete; do not load unbounded files into memory.
- Detect binary content and decode text strictly. Replacement decoding may be used only for display snippets, never as the canonical content inspected by a rule.
- Preserve file identity, mode, encoding, BOM and line-ending metadata in findings. Avoid disclosing secret contents in reports.

### 3.2 Contract and rule analysis

- Validate JSON contracts against their declared schemas and schema versions; a successful JSON parse is not schema validation.
- Every rule has a stable ID, version, severity, category, rationale, scope, evidence requirements and a test fixture.
- Distinguish a definite violation from a heuristic hint. A textual pattern is not proof of unsafe behavior.
- Allow narrow, documented suppressions with an owner, reason and expiry. Suppressions must not silence critical invariants.
- Report exact source spans/paths, rule ID, evidence, confidence class and remediation. Avoid dumping secrets or full proprietary source snippets.
- Build the improvement-conflict matrix from explicit contract data. Never silently resolve conflicts by dropping warnings or changing input policy.
- Keep repository-security findings separate from malware verdicts and from the Reaper defense-context taxonomy. Context tags describe subject matter; they do not prove malicious code.

### 3.3 Deterministic output

- The report schema is versioned and rejects unknown mandatory semantics.
- Findings are sorted by stable path, span, rule ID and evidence key.
- Separate nondeterministic run metadata (wall clock, host name) from the canonical deterministic result digest.
- Record tool version, ruleset digest, contract versions and repository commit/index identity.
- Exit status is explicit: invalid invocation, audit infrastructure failure, policy violation and successful audit are distinct outcomes.
- A report MUST state coverage: files seen, skipped, excluded, bytes scanned and reasons for incomplete inspection.

### 3.4 Patch proposal and safe application

The audit worker MUST NOT rewrite source files in place as a side effect of analysis.

A suggested fix is initially a patch proposal with source digest, target path, expected content digest, rationale and tests. Applying it is a separate operation requiring explicit user/developer action.

When an apply workflow is later implemented, it MUST:
1. Revalidate repository root and ensure each path remains inside it.
2. Reject symlink targets and verify the current file digest still matches the reviewed patch base.
3. Preserve executable mode, file permissions, encoding, BOM and declared line endings.
4. Write to a same-filesystem staging file, flush according to the durability contract, then atomically replace.
5. Keep a recoverable original or patch artifact and report each file's committed/rolled-back state.
6. Stop on unexpected concurrent modification rather than overwriting newer work.
7. Support dry-run and per-file review. It must not bulk-normalize all source files by default.

The source proposal's apply_whitespace_fixes uses direct write_bytes after normalization. It does not implement atomic replacement, repository containment checks, symlink protection or a backup. That behavior MUST NOT be used as the production patch-application design.

## 4. UX and local workbench integration

The audit service and future Reaper Studio/workbench panels must follow the DuckOS interaction and ergonomics standard where integrated into the Duck environment.

- Run scans and compiler analysis outside the editor's input/render thread.
- Debounce incremental analysis and cancel obsolete requests.
- Use bounded queues and explicit backpressure. Do not let a busy project flood the UI with stale diagnostics.
- Keep diagnostics attached to stable source spans and source-map identities.
- Preserve open buffers, cursor positions, unsaved edits, filters, selected diagnostics and workspace layout.
- Group findings by severity, rule and subsystem. Expose a clear route from summary to exact source span and remediation.
- Acknowledge an action immediately; distinguish queued, running, partial, completed, cancelled and failed.
- Make report generation local and quiet by default. Do not upload source files, reports or telemetry unless explicitly requested.
- Support keyboard navigation, visible focus, screen-reader semantics, text scaling, reduced motion and Comfortable/Standard/Compact density.
- A failed or cancelled audit must not discard editor state or block ordinary editing.

## 5. flow_guard.c proposal review

The C ring-buffer sample in OS(2).txt is a conceptual reference, not a verified Reaper runtime component. A repository search did not find flow_guard.c or the proposed fg_ring_pop implementation in the inspected Reaper default branch. The sample contains correctness defects that must be fixed before any equivalent implementation is accepted.

### 5.1 Confirmed sample defects

1. fg_ring_pop consumes the frame header before checking whether dst_capacity can hold the payload. When it returns FG_ERR_FRAME_TOO_LARGE, the header has been removed but the payload remains. The next call then interprets payload bytes as a new header.
2. For a non-empty payload and dst_payload == NULL, the conditional copy is skipped while the function can still return FG_OK. The payload remains queued after the header was consumed, desynchronizing the next pop.
3. The API does not establish whether the ring is single-threaded, single-producer/single-consumer or multi-producer/multi-consumer. Plain cursor/counter updates are not thread-safe.
4. The frame header is copied as a native C struct. Padding, alignment and byte order are not defined as a stable wire/storage layout.
5. high_water_mark == 0 is accepted by initialization, causing every successful write to satisfy the watermark test.
6. The corruption path resets the queue but returns FG_ERR_EMPTY, conflating malformed internal state with ordinary emptiness.
7. watermark_hits increments for every write while the queue remains above the threshold; that is not the same as counting threshold crossings.

These findings are derived from the sample in OS(2).txt, not from a shipped Reaper implementation.

### 5.2 Required ring/queue contract before implementation

- State the ownership model explicitly. A simple SPSC queue is acceptable only when producer/consumer identity and memory-ordering rules are enforced. Do not imply MPSC/MPMC safety without a separately verified algorithm.
- Validate initialization and all capacity arithmetic before any subtraction or addition that could underflow/overflow.
- Validate the complete frame (header plus payload) before committing cursor changes.
- Implement a peek/validate/copy/commit read transaction. An undersized destination returns the required size without consuming the frame. A null destination for a non-empty payload is an invalid argument and consumes nothing.
- Provide distinct empty, full, malformed-frame, capacity, invalid-argument and cancelled states.
- Define counter overflow behavior and whether high-/low-water metrics count transitions, durations or individual observations.
- Define a fixed, versioned byte representation if frames cross process, machine or persistent-storage boundaries; never rely on implicit native struct layout.
- Specify whether a checksum, sequence number or generation marker is required. Corrupt frames must not silently masquerade as an empty queue.
- Document who owns storage and how initialization, reset and teardown synchronize with active producers/consumers.

Minimum tests: wrap-around at each header/payload boundary; zero-length and maximum frames; full/empty transitions; undersized destination with subsequent successful retry; null destination; corrupted/oversized length; arithmetic extremes; invalid/uninitialized ring; watermarks; counter wrap; randomized model comparison; fault injection; and concurrency tests for the exact declared ownership model.

Do not insert the source sample into a hot path until it passes this contract. The eventual DuckOS-owned system implementation should use Reaper as the primary systems language once the required native memory, ABI and atomic operations are available. Any temporary C adapter must remain a narrow, separately tested bootstrap boundary.

## 6. Self-host rewrite proposal review

The self_rewrite_executor example in OS(2).txt is not a semantic translator and MUST NOT be run against repository files.

Specific problems:

- strip_python_dependencies changes candidate metadata and sets deterministic_guaranteed: true without analyzing or proving behavior.
- build_native_reaper_module emits a generic pass-through stream node. It does not translate the original script's functions, arguments, side effects, data formats, errors or exit behavior.
- The executor can therefore report Accepted and removed_python_hooks: 1 even though the original behavior was not preserved.
- The fs::move_atomic result is not checked before computing the final digest and reporting success.
- The generated module name is derived from a file stem without an explicit identifier/path sanitization contract.
- The sample does not define source-map preservation, differential behavior tests, dependency migration, rollback after publication, crash recovery or a proof that the old program remains available until the replacement is verified.

A file extension change, an empty wrapper, or a successful compile is not evidence of semantic equivalence.

### 6.1 Safe migration transaction

Every migration candidate follows this transaction:

1. Inventory: identify exact source paths, owners, callers, dependencies, CI entry points, data formats, side effects and licence/provenance.
2. Classify: record whether it is compiler core, DuckOS system code, host tooling, test harness, generated/vendor code or third-party dependency.
3. Specify: define observable behavior, stable inputs/outputs, errors, exit codes, environment assumptions and resource/effect budgets.
4. Build parallel: implement the Reaper replacement without deleting or mutating the reference implementation.
5. Differential verification: compare outputs, diagnostics, side effects and failure behavior across golden and adversarial fixtures.
6. Determinism and quality gates: run repeatability, ABI, resource-bound, security and improvement-conflict checks.
7. Stage and review: publish the candidate as a separate artifact/PR with source digest, generated diff, test evidence and rollback reference.
8. Canary/cutover: enable the replacement only for a declared target/workflow; retain the prior implementation for rollback.
9. Retire: remove the old implementation only after the replacement owns all supported call sites and CI proves parity across the declared matrix.

No stage may invent a behavior-preservation flag. The evidence must be computed from actual tests and the declared contracts.

## 7. Delivery stages

| Stage | Deliverable | Exit evidence |
|---|---|---|
| AUD-0 | Repository inventory, contract ownership and source/CI map | Stable inventory; no mutation; explicit exclusions |
| AUD-1 | Read-only audit report contract and versioned rules | Valid schema, deterministic ordering, bounded read coverage and rule fixtures |
| AUD-2 | Safe patch proposal/apply protocol | Symlink/path/concurrency tests; atomic replace/rollback; dry-run proof |
| FG-0 | Formal ring-buffer semantics and failure model | Ownership model, fixed frame representation and boundary-state table |
| FG-1 | Ring/queue reference implementation in the correct native target | Correctness, model, fuzz, fault-injection and concurrency evidence |
| SELF-0 | Python/host-tool inventory and migration classification | All candidates classified; critical paths and maintainers mapped |
| SELF-1 | Reaper-native compiler/contract primitives | Stable IR, Span/SourceMap, effect model and deterministic serializer |
| SELF-2 | First semantic-equivalent self-host replacement | Differential tests, rollback drill, repeatable output and CI parity |
| SELF-3 | Incremental retirement of duplicate host logic | No orphaned callers; all supported CI paths pass on target matrix |

The planned registry and these delivery stages are architecture artifacts. They do not claim that the audit worker, native ring buffer, self-host rewriter or full native test runner exists today.

## 8. Cross-repository contract edges

- DuckOS: Reaper-native services consume versioned syscall, DABI64, capability, process, IPC, storage and diagnostic contracts. Reaper policy tests do not prove kernel enforcement.
- Native Desktop / Mora: Workbench behavior follows the ergonomics standard; native focus, input, compositor, DPI and accessibility claims require platform evidence.
- BAV: Beelzebul repository assurance, context-only taxonomy and DuckOS endpoint BAV remain distinct. Context metadata must never become malware evidence.
- Reaper language formats: all planned formats and extension ownership are recorded in FILE_FORMATS_AND_EXTENSIONS_V1.md. .bav belongs to DuckOS BAV; Reaper buffer contracts use .bufspec.

## 9. Source traceability

- OS(2).txt application/workbench ergonomics checklist: lines 805–812.
- Repository polisher proposal and contract-first strategy: lines 813–1324 and 1325–1740.
- flow_guard.c ring-buffer sample: lines 1740–1948.
- Self-host and Python decommission proposal: lines 1949–2264.
- File-format family and conceptual Reaper extension sample: lines 2265–2597.

The source's purpose and architecture are preserved; unsafe or unverified implementation details are called out rather than silently treated as correct.
