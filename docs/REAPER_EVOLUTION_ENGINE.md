# REAPER Evolution Engine

## Purpose

The Evolution Engine is the deterministic quality-control loop for language and
tooling development. It inventories the implementation, checks Python syntax,
runs the repository test suite, and reports concrete test-coverage opportunities.

It is deliberately **not** an unconstrained self-modifying agent. A tool that
rewrites its own compiler without a semantic oracle can silently corrupt the
language, erase compatibility, or weaken safety. The current engine therefore
does not edit source files, install dependencies, execute generated code, or
merge branches.

## Current implementation

Run:

```bash
python -m reaper --evolve
python -m reaper --evolve --iterations 3
```

Each bounded cycle performs:
1. In-memory syntax compilation of every `reaper/**/*.py` file.
2. The standard-library unittest suite in a subprocess with a timeout.
3. A proposal scan that compares implementation modules with test references.
4. A machine-readable JSON report with durations, pass/fail status and proposals.

The filename-based coverage scan is a heuristic, not coverage instrumentation.
A passing report is not a security audit, a proof of correctness, or permission
to merge automatically.

## Evolution pipeline

```text
Language proposal
  -> syntax/spec change
  -> parser + AST + typed IR implementation
  -> positive and negative conformance tests
  -> fuzz + differential tests
  -> compatibility + resource-limit checks
  -> benchmark comparison
  -> human-reviewed pull request
  -> merge after required CI succeeds
```

### Required invariants

- Preserve Reaper's existing syntax and `~>` semantics unless a versioned change
  explicitly authorizes otherwise.
- МОСТ is an exact Russian keyword-alias table over REAPER. It must use the
  existing REAPER parser, AST, typed IR and runtime; no intent frontend or fork.
- Never infer permissions from source text. Filesystem, network, process and
  hardware effects require explicit capability boundaries.
- No generated patch is accepted without tests that fail before the patch and
  pass after it.
- Performance changes must include reproducible before/after measurements.
- Every evolution cycle is bounded, deterministic where possible, and leaves
  the working tree untouched.

## Roadmap

### E0 — Quality loop (implemented)
Syntax checks, bounded test execution, JSON reports and improvement proposals.

### E1 — Language knowledge base
Versioned grammar, operator/type/effect registries, feature dependency graph,
diagnostic catalogue and compatibility snapshots.

### E2 — Verified code improvement
AST-aware refactor proposals, patch previews, property-based tests, fuzzing,
differential execution against the Python compatibility interpreter, and
rollback on any failed gate. Generated patches remain reviewable artifacts.

### E3 — Compiler self-hosting
Native C17 lexer/parser, typed AST, canonical typed IR, verifier, ownership and
effect analysis, followed by native backend parity. Self-hosting starts only
after semantic parity and reproducible bootstrap builds are demonstrated.

### E4 — REAPER IDE
A separate developer application with a project explorer, tabbed editor,
language-aware syntax highlighting, diagnostics, completion, hover docs,
rename/references, formatter, integrated terminal, test runner, debugger,
IR/AST inspector, profiler and evolution dashboard. The IDE must consume
versioned language-server/compiler APIs; it must not be embedded in the runtime.

## Acceptance gates

A feature is complete only when its specification, implementation, tests,
documentation and compatibility impact are all recorded. The system may
recommend an improvement automatically; it may not claim implementation or
merge unverified code.
