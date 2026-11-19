# Native Language and Tooling Quality Standard

## Purpose

Reaper is a flow-first language and toolchain. The language, interpreter/compiler, developer tools, and any desktop interface must evolve as a coherent system without coupling the language runtime to a particular UI.

## Engineering principles

1. **Natural syntax:** syntax and diagnostics should read clearly, remain consistent, and avoid surprising implicit behavior. Prefer precise semantics over decorative syntax.
2. **Native architecture:** keep the language specification independent from execution backends. The Python interpreter remains a useful reference implementation; native C17 compiler/runtime components must have explicit parity goals and conformance tests.
3. **Composable capabilities:** extend shared AST, semantic IR, runtime, and standard-library primitives rather than duplicating functions. Every new function/operator needs a defined signature, typing/effect rules, error behavior, and compatibility impact.
4. **Deterministic execution:** resource limits, evaluation order, errors, serialization, and compiler output must be predictable and testable.
5. **White / red / blue design system:** for future desktop tooling, use neutral/white surfaces, restrained red for errors and destructive actions, and blue for primary actions, focus, and informational states. Preserve accessibility, keyboard navigation, and native platform conventions.
6. **Separation of concerns:** language core and CLI remain headless; IDE/desktop features consume stable public APIs and must not become runtime dependencies.

## Verification contract

- Lexer, parser, AST, semantic analysis, IR, runtime, standard library, and CLI each have focused tests.
- Every public built-in and operator has positive, negative, boundary, and error-path coverage where applicable.
- Maintain shared conformance fixtures across Python and native implementations.
- Use property-based and fuzz testing for lexer/parser input, serialization, and runtime boundaries.
- Test resource limits: step budget, call depth, collection size, and text length.
- Verify deterministic AST/IR JSON and stable diagnostics.
- Native builds use strict warnings and sanitizers where supported; Python tests run across supported interpreter versions.

## Automation and release safety

- CI may validate, build, test, package, and publish review artifacts.
- Automation may create/update isolated branches and open pull requests.
- No force-pushes, branch-protection bypasses, self-approval, or unattended merges to `main`.
- Generated code and self-improvement proposals must be deterministic, bounded, diff-limited, tested, and reviewable.
- Self-hosting or autonomous evolution must never execute untrusted generated code in privileged CI contexts.
- Workflow permissions are least-privilege; secrets are not exposed to forked pull requests.

## Desktop and IDE direction

- Treat a native desktop IDE as a separate application layer over stable compiler, diagnostics, formatting, project, and debug APIs.
- Keep CLI and batch compilation fully functional without a GUI.
- Provide editor, diagnostics, AST/IR inspection, project navigation, test execution, and debugger integration incrementally.
- Autostart, background agents, and update checks are opt-in, visible, and reversible.

## HMGA v3: deterministic, bounded evolution

The iteration hierarchy expresses orchestration depth; it is not permission to run unbounded recursive generation or to multiply every function into every other function. Each pass declares finite CPU/time, memory, diff-size, test, and retry budgets.

1. **Inventory:** record the exact `main` SHA, open PR heads/bases, active branches, feature IDs, CI evidence, and supported compiler/runtime targets.
2. **Dependency graph:** model parser, semantic IR, optimizer, runtime, standard library, and IDE dependencies as a directed acyclic graph. Stacked PRs are promoted in dependency order; a child PR is not treated as independently mergeable.
3. **Capability registry:** assign stable IDs and versioned contracts to language features, built-ins, compiler passes, runtime services, and IDE integrations. Record signatures, types, effects, errors, compatibility, and acceptance tests.
4. **Cross-application matrix:** test each declared compatible edge through shared contracts and canonical IR. Do not fabricate combinations between semantically unrelated capabilities; mark them explicitly not applicable.
5. **Bounded retries:** retry only transient runner or infrastructure failures within a configured attempt budget. Reproducible parser, type, optimizer, or test failures must be diagnosed and fixed.
6. **Evidence record:** retain exact source/base SHAs, toolchain versions, conformance results, compatibility notes, security review, and rollback path for every proposal.

## Deterministic promotion to main

- Implement each coherent capability layer on an isolated branch and publish a PR against `main` (or a documented prerequisite PR when genuinely stacked).
- Validate the proposed merge result on the exact head/base pair. The promotion job must re-read both SHAs after validation and stop if either changed.
- Require the Python compatibility suite, native C17 build/tests, relevant conformance/fuzz checks, and an approval from someone other than the PR author.
- When `main` advances, refresh the branch through normal GitHub operations and rerun all relevant checks; never merge a stale result just because an earlier run passed.
- GitHub native auto-merge may be enabled only after independent approval and validation. Repository branch protection remains authoritative.
- No direct writes to `main`, force-pushes, approval fabrication, test bypasses, or execution of untrusted generated patches. Missing, pending, failed, or inconclusive evidence blocks promotion.

## Improvement loop

Inspect current semantics → define a versioned contract → implement a minimal composable change → add conformance and regression tests → run cross-version/cross-backend CI → review security and UX → document migration → submit a pull request. Apply each shared improvement to every relevant function only when semantics match; do not create exponential duplicate APIs.

## Acceptance criteria

A change is ready when semantics are specified, tests cover normal and failure behavior, supported implementations agree, resource limits hold, diagnostics are actionable, exact-SHA evidence is attached, independent review is complete, and rollback is straightforward.
