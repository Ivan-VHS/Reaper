# REAPER Autonomous Evolution System (C17)

## Purpose

The evolution engine is part of the native C17 toolchain, not a Python runtime
feature. It governs how proposed changes to the language, compiler, optimizer,
runtime, standard library and IDE earn acceptance.

The first native increment is an **evidence gate**, not an autonomous source
rewriter. It is deliberately deterministic and fail-closed. It cannot edit
source, execute generated patches, grant capabilities, approve its own work,
or merge branches.

## Native C17 implementation

Files:
- `include/reaper/evolution.h`: public evidence, policy and decision contract.
- `src/evolution.c`: deterministic readiness evaluator and status output.
- `tests/test_evolution.c`: positive, negative, security, rollback, benchmark
  and human-approval gate tests.

Build and run:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/reaper-c --evolution-status
```

Default evidence thresholds are at least one positive test, one negative test,
1,000 fuzz cases and 100 differential cases. Every candidate also needs a
specification, implementation, compatibility check, security review and
rollback path. If a performance improvement is claimed, both measurements
must be present and the after measurement must be lower. These thresholds are
minimum gates, not mathematical proof of correctness.

A candidate with all technical evidence but no maintainer approval is marked
`review-required`. Only a maintainer-approved candidate can become
`ready-for-maintainer`; this status still does not merge code. Merge remains
a repository governance action after CI and review.

## Evolution loop

```text
Observe implementation + test/benchmark evidence
  -> identify a bounded improvement opportunity
  -> write versioned language/ABI/behavior specification
  -> generate a patch proposal (future phase; never auto-apply here)
  -> build and run positive + negative conformance tests
  -> fuzz and differential-test against compatibility oracle
  -> verify compatibility, security, effects and resource limits
  -> retain rollback snapshot and reproducible benchmark evidence
  -> maintainer review and CI
  -> merge through normal repository policy
  -> update implementation ledger and feature registry
```

## Architecture and ownership

- REAPER remains the language; MOST remains a semantic frontend.
- Both frontends must converge on the same typed canonical IR.
- The C17 compiler and evolution gate are the native destination.
- Python is a temporary compatibility oracle until full differential parity;
  it is not required by the final native build.
- A proposal cannot add keywords, effects, built-ins or ABI behavior without a
  versioned specification and explicit compatibility impact.
- Every optimizer pass must preserve observable semantics, reject malformed IR,
  avoid undefined behavior and be deterministic.
- Every generated patch must be reviewable and reversible.

## Roadmap

### EV0 — Evidence gate (implemented)
Native C17 API, fail-closed decision bitset, thresholds, benchmark-claim checks,
maintainer approval gate, CLI status report and unit tests.

### EV1 — Native repository auditor
Walk source/headers/tests/docs, identify orphaned symbols, missing tests,
stale docs and duplicated feature IDs. Emit stable JSON proposals with exact
file/line evidence. No writes.

### EV2 — Reproducible optimizer pipeline
Pass registry, dependency ordering, fixed-point iteration budgets, IR verifier
between passes, semantic differential tests and per-pass performance counters.

### EV3 — Patch proposal engine
AST/IR-aware change plans, minimal diffs, generated regression tests and
rollback snapshots. Proposed patches remain unapplied until explicit approval.

### EV4 — Compiler and language evolution
Versioned grammar, typed symbols, ADTs, effects/capabilities, ownership/regions,
MOST intent resolution and full typed IR. Each feature has a unique ID,
dependencies, acceptance tests and status.

### EV5 — REAPER IDE
Native language-server protocol, syntax highlighting, completion, diagnostics,
hover documentation, rename/references, formatter, debugger, AST/IR viewer,
profiler, test explorer, build panel, Git review and evolution dashboard.

### EV6 — Self-hosting
Bootstrap compiler, reproducible stage0/stage1 builds, source-to-source
differential conformance and independent verification. Self-hosting is complete
only when the compiler can rebuild itself reproducibly and pass the full suite.

## Non-goals and safety

No infinite loops, fictitious feature counts, automatic main-branch writes,
unreviewed code execution, hidden network access, or automatic permission
expansion. The engine is bounded by explicit budgets. A billion requested
iterations is not a useful correctness criterion; reproducible evidence and
verified convergence are.
