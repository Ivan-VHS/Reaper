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
- No force-pushes, branch-protection bypasses, or unattended merges to `main`.
- Generated code and self-improvement proposals must be deterministic, bounded, diff-limited, tested, and reviewable.
- Self-hosting or autonomous evolution must never execute untrusted generated code in privileged CI contexts.
- Workflow permissions are least-privilege; secrets are not exposed to forked pull requests.

## Desktop and IDE direction

- Treat a native desktop IDE as a separate application layer over stable compiler, diagnostics, formatting, project, and debug APIs.
- Keep CLI and batch compilation fully functional without a GUI.
- Provide editor, diagnostics, AST/IR inspection, project navigation, test execution, and debugger integration incrementally.
- Autostart, background agents, and update checks are opt-in, visible, and reversible.

## Improvement loop

Inspect current semantics → define a versioned contract → implement a minimal composable change → add conformance and regression tests → run cross-version/cross-backend CI → review security and UX → document migration → submit a pull request. Apply each shared improvement to every relevant function only when semantics match; do not create exponential duplicate APIs.

## Acceptance criteria

A change is ready when semantics are specified, tests cover normal and failure behavior, supported implementations agree, resource limits hold, diagnostics are actionable, and rollback is straightforward.