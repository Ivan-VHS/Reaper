# Ivan-VHS Code Style

**Status:** active engineering standard  
**Version:** 1.0  
**Established:** 2026-11-25  
**Scope:** Ivan-VHS repositories and their cross-repository interfaces

## Purpose

This standard turns recurring preferences from the personal engineering profile into rules that can be reviewed in code. It is not a personality diagnosis and does not infer engineering ability or character from a photograph. The photo is visual context; the rules below come from stated preferences and repeated project decisions.

The working character is **собранная ясность**: independent thinking, deliberate architecture, natural code, exact boundaries and evidence of working behavior.

The short rule is:

> Think broadly. Change narrowly. Verify completely.

## 1. The working sequence

Use four roles in order:

1. **Architect** — understand the real problem, affected components, contracts and constraints.
2. **Editor** — remove ambiguity, duplicated behavior, unnecessary layers and requirements that do not belong to this change.
3. **Engineer** — implement the smallest complete vertical slice with explicit ownership and failure behavior.
4. **Verifier** — build, run relevant tests, inspect the diff and record what is and is not proven.

Do not let the architect keep expanding the scope while the engineer is trying to finish the current slice. Preserve new ideas in the backlog rather than silently adding them to an active change.

## 2. Readability is part of correctness

- Write code as a person will have to debug it six months later.
- Use domain names that explain intent. Short names are appropriate for local indices and conventional loop variables; they are not a substitute for meaningful names in business or system logic.
- Put one logical operation on a line. Do not compress control flow, declarations or error handling to save lines.
- Keep functions cohesive. Split a function when the new unit has a clear responsibility or makes a meaningful invariant easier to see.
- Prefer direct control flow and early validation over deep nesting.
- Keep abstractions proportional to real use. Do not add a framework for one caller; generalize when multiple real consumers share the same contract.
- Comments explain why a constraint or non-obvious decision exists. They do not narrate code that is already clear.
- Preserve the host language's idioms. Do not impose one naming scheme or language on every repository.

Readable code is not verbose code. Remove ceremony as confidently as duplication.

## 3. Contracts before cleverness

For each public boundary, make the following explicit where applicable:

- accepted inputs and rejected states;
- output shape and invariants;
- ownership, lifetime and cleanup responsibility;
- mutation and other side effects;
- error representation and recovery behavior;
- resource limits and integer-width assumptions;
- synchronization and thread-safety guarantees;
- compatibility and versioning.

Do not make callers infer ownership or failure behavior from implementation details. Do not silently discard errors that can affect correctness.

## 4. Defensive implementation

Treat external input, persisted data, device responses and cross-process messages as untrusted.

- Validate lengths, counts, enum values, offsets and version fields before use.
- Check addition, multiplication, alignment and conversion before the operation can overflow or truncate.
- Keep bounds checks next to the access they protect.
- Make cleanup correct on every failure path.
- Prefer explicit state transitions to hidden global state.
- Keep privileged, unsafe and hardware-facing operations behind narrow interfaces.
- Default to local and read-only behavior when a task does not require mutation or network access.
- Do not log secrets or raw private user data.
- Security-sensitive decisions fail closed unless the contract explicitly specifies another safe behavior.

Do not add defensive checks that cannot fail under the documented type and contract. The goal is meaningful protection, not noise.

## 5. Determinism and operational clarity

Where the product requires repeatability:

- keep ordering stable;
- avoid dependence on ambient locale, clock, network or mutable process state unless explicitly required;
- make resource limits visible;
- report failures with the responsible component and useful location or context;
- keep diagnostics free of secrets;
- make important operations reproducible from documented commands.

Performance work must identify the measured bottleneck. Do not trade away clarity for an unmeasured optimization.

## 6. Tests that describe behavior

Every non-trivial change should have relevant evidence:

- a normal successful case;
- invalid input and failure-path coverage;
- boundary and overflow coverage where relevant;
- regression coverage for the behavior being fixed;
- repeatability or concurrency coverage when the contract needs it.

Tests should assert public behavior and invariants, not mirror private implementation line by line. Prefer the repository's native test and build systems. A test that was not run must be reported as not run.

For compiler and language work, keep lexer, parser, semantic, IR and backend tests aligned with the same language contract. For operating-system work, test the narrowest real boot, memory, ABI or service path that proves the change.

## 7. Cross-repository discipline

- Preserve each repository's purpose, native language, build system and established public API.
- Do not migrate a module to another language merely to make style look uniform.
- When changing a shared contract, inspect its consumers and update the necessary adapters, tests, schemas and documentation in the same planned change set.
- Keep changes focused. Do not bundle unrelated cleanup into a behavior fix.
- Respect third-party licenses, attribution and provenance. Inspiration is not permission to copy implementation.
- For DAK, keep Reaper as the intended native language direction, but do not describe bootstrap components as Reaper-based until the actual toolchain and target ABI support them.

## 8. Naming and formatting

Follow the repository's formatter and language conventions first. Where a repository has no established rule:

- C functions and variables use descriptive snake_case; macros use uppercase names; existing public type names remain stable.
- C and C++ control flow uses braces consistently, one statement per line and explicit conversions at meaningful type boundaries.
- Python uses standard Python naming and formatting; it is not a default implementation or test-runner choice for DAK work.
- Reaper examples use the canonical language syntax and the documented semantic meaning of each operator.

Do not perform a repository-wide formatting sweep as a side effect of a targeted fix.

## 9. Review and delivery

A reviewable change states:

1. the defect or limitation being addressed;
2. the smallest intended scope;
3. the contract that must remain true;
4. the tests and commands used;
5. the evidence obtained and the remaining limitations.

Use a dedicated branch and a focused pull request. Keep main protected. Separate unrelated concerns into separate reviewable changes. Do not mark a planned, prototype or partially implemented feature as verified.

## 10. Definition of done

A change is complete only when:

- the intended behavior is implemented, not just described;
- its public contract and failure behavior are understandable;
- relevant tests pass, or the unverified parts are explicitly named;
- the diff contains no accidental unrelated changes;
- documentation reflects the actual implementation state;
- dependent repositories and interfaces have been considered.

**Final decision rule:** when an abstraction, optimization or extra feature does not improve correctness, safety, maintainability or measured performance, leave it out.
