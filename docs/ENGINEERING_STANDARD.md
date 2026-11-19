# Engineering Standard

Status: repository-wide development contract  
Applies to: MOST syntax, Python interpreter, experimental native C17 core, CLI, tests, CI, documentation and future UI work

## 1. Natural, coherent language design

- Prefer readable, consistent syntax and explicit semantics over clever shorthand.
- Keep the left-to-right flow operator (~>) predictable. A function should compose naturally when its input and output contracts agree.
- Add a language feature only when it solves a distinct problem and has a documented semantic contract. Do not inflate the language with aliases or placeholder functions.
- Preserve immutability-by-default, explicit mutation and bounded execution. Errors should remain understandable and source-aware.
- Keep the Python compatibility interpreter and native C17 workstream clearly separated until full conformance parity is demonstrated.

## 2. Function composition and interaction coverage

"Apply every function to every function" means test every *valid, signature-compatible interaction*, not blindly execute an N×N Cartesian product.

1. Inventory built-ins and user-function contracts: arity, accepted types, result types, effects, limits and errors.
2. Identify valid function pairs and representative multi-stage flows.
3. Add positive tests for those pairs and chains, including order-sensitive cases such as map → keep → fold.
4. Add negative tests for incompatible values, invalid arity and resource-limit boundaries.
5. Use exhaustive combinations only for small finite domains; use pairwise or risk-based coverage for larger spaces.
6. Document intentionally unsupported combinations instead of silently coercing values.

A feature is implemented only when the runtime behavior and conformance tests exist. Roadmap entries, system-track labels and partial native IR support are not proof of a complete language feature.

## 3. Tests and automatic execution

- Run syntax compilation and the complete standard-library unittest suite.
- Validate checked-in examples in check-only mode and run the designated executable examples.
- Preserve the separate native C17 build, native tests and CLI smoke tests.
- Test all supported Python versions in the CI matrix.
- CI may start automatically on feature-branch pushes and pull requests; manual dispatch remains available for controlled diagnostics.
- Workflows must be bounded and least-privilege (contents: read unless a narrowly scoped write is essential).
- Do not create self-triggering, unbounded recursive workflow loops.

## 4. Push, review and merge policy

- Work on a dedicated feature or maintenance branch. Never push directly to main, force-update it, or bypass repository controls.
- Automation may validate a change and prepare a PR. It must not approve its own work.
- Merge only when applicable CI checks are green, an independent human review is complete, and repository rules permit the merge.
- Do not enable unattended auto-merge without independent approval and required status checks.
- Preserve a simple rollback path by reverting the isolated PR or commit.

## 5. Native and desktop application boundary

The current product has a Python 3.10+ interpreter/CLI and an experimental native C17 workstream. The native workstream includes an early lexer, expression parser/AST, limited IR/lowering and bring-up CLI; it is not yet a full native interpreter/compiler with complete language parity.

There is no desktop GUI at this milestone. The white–red–blue design vocabulary is the default for future first-party UI work:

- White surfaces: #FFFFFF.
- Blue primary actions and focus: #1D4ED8.
- Red destructive actions and warnings: #DC2626.
- Neutral text: #111827; secondary surfaces: #F8FAFC.

Use semantic labels and icons as well as color, retain keyboard navigation and visible focus, and check text contrast. Do not add UI dependencies to the interpreter's runtime merely to satisfy a visual theme. A desktop application is a separate milestone requiring an approved UI architecture, platform scope, UI tests and packaging before it can be described as available.

## 6. Feature lifecycle and maintainability

Every new feature must have:
- a problem statement and testable acceptance criteria;
- a concise syntax/API contract and defined failure behavior;
- unit and composition tests for compatible interactions;
- updated language reference, examples and applicable translations;
- supported-version and compatibility notes;
- a migration or rollback strategy.

Keep modules focused, avoid duplicate evaluator logic, make effects explicit, and keep optional developer tooling outside the required runtime dependency set.

## Definition of done

A change is complete when implementation, tests, examples, documentation, CI evidence and review agree. Planned, experimental or heuristic work must be labeled accurately.
