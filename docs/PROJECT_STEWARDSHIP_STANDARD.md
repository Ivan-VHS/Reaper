# Project stewardship and anonymous operating principles

**Status:** normative project-governance guidance. It defines review expectations and communication standards; it does not claim that every organizational practice is enforced by the runtime.

## Purpose

Evolve a reliable programming language and execution environment through disciplined delivery, transparent authority, respectful collaboration and evidence-led public claims. The project should earn trust through semantics, diagnostics, bounded execution and reproducible behavior—not through hype or feature-count theater.

## Operating principles

1. **Meaning before visibility.** Prioritize language capabilities that solve real programming problems. Promotional reach, registry size and headline counts are not substitutes for usable, tested behavior.
2. **Discipline with explicit status.** Every language feature and native capability must be marked implemented, partial, planned or not applicable according to its actual code and verification evidence.
3. **Authority follows the boundary.** Parser, runtime, compiler, editor, FFI and security decisions have explicit owners and review paths. Informal influence never silently overrides a technical contract.
4. **Evidence over status.** Review proposals using semantics, tests, compatibility and threat models—not the author's seniority, identity, age or relationships.
5. **Adaptive communication.** Use concise written updates for routine progress, focused design discussions for ambiguity and durable records for decisions affecting syntax, runtime behavior or trust.
6. **Continuity over heroics.** Keep design rationale, migration paths, release procedures and incident knowledge in the repository so the language does not depend on one always-available maintainer.

## Decision record

For changes to syntax, canonical symbols, runtime permissions, native lowering, optimization or external interfaces, record:

- **Problem and expected outcome.**
- **Decision owner and affected maintainers.**
- **Semantic contract and compatibility implications.**
- **Evidence:** implementation, conformance tests, error cases and known gaps.
- **Alternatives and rejected trade-offs.**
- **Failure containment, rollback and review trigger.**

For small reversible improvements, a focused pull-request description is sufficient. For changes that can alter program meaning, security or persisted artifacts, include a design note and migration guidance.

## Execution rhythm

1. **Intake:** classify work as language semantics, runtime behavior, tooling, documentation, security or release maintenance.
2. **Specify:** define syntax, types, limits, side effects, diagnostics and compatibility before implementation.
3. **Implement:** make the smallest coherent change and keep the Python reference and native implementation status explicit.
4. **Verify:** run unit, conformance, parser, runtime and native tests relevant to the change; keep failing cases reproducible.
5. **Communicate:** update examples, registries, user documentation and release notes in the same change where possible.
6. **Review:** capture regressions, compatibility breaks and user feedback as owned follow-up tasks.

Limit concurrent architectural rewrites. Prefer incremental changes that preserve diagnostic quality and make behavior easy to compare.

## Communication, feedback and public credibility

- Separate implemented behavior from proposals, generated catalogs, research profiles and future targets.
- Distinguish a feature specification from an executable implementation. A registry entry is not evidence that the runtime supports it.
- Describe runtime guarantees narrowly. In-process native extensions are trusted code, not a sandbox for untrusted modules.
- Treat community feedback as evidence to investigate. Record minimal reproduction programs, expected behavior, actual behavior and affected versions.
- Prioritize reports by correctness, security impact, user reach, reproducibility and confidence—not by online attention.
- For incidents, communicate confirmed impact, affected versions, mitigation and next update. Correct inaccurate statements when facts change.
- Avoid manufactured controversy, inflated counts, false compatibility promises and urgency that is not supported by a real risk.

## Incident and conflict protocol

Apply **stabilize → assess → contain → communicate → recover → review**. Preserve a minimal reproducer and relevant logs; disable or roll back a harmful release where possible; publish a clear advisory; verify the fix across reference and native paths; and document a blameless retrospective. Keep vulnerability details in the designated private reporting channel until disclosure is safe.

## Sustainable stewardship

Maintain a risk register for language compatibility, runtime permissions, native parity, FFI trust, supply chain and release continuity. Convert long-term direction into milestones with observable completion criteria. Keep personal and family details out of source examples, telemetry, screenshots and issue discussions unless their disclosure is both necessary and explicitly authorized.

Professional opportunities, access and credit must be role-neutral. Respectful disagreement is expected; harassment, retaliation, hidden decision authority and personal attacks are not acceptable substitutes for technical review.

## Reaper-specific acceptance gates

- Every syntax or runtime change includes tests for success, invalid input, boundary conditions and failure semantics.
- Canonical symbols and aliases remain consistent across the parser, runtime, documentation and generated catalogs.
- Native C17 parity is claimed only for behavior covered by native implementation and conformance tests; Python reference behavior must not be silently described as native support.
- Execution quotas, permission grants, audit behavior and revocation semantics remain explicit and fail closed where required.
- FFI boundaries identify trusted-code assumptions, ownership rules, ABI versions and error propagation.
- Public function counts and maturity statements must match the current registry and implementation status.

## Release review checklist

- [ ] The change has a clear user-facing or engineering outcome.
- [ ] Semantics, side effects, quotas and compatibility are documented.
- [ ] Tests cover normal, invalid and boundary cases.
- [ ] Native/reference status is accurate and parity is not overstated.
- [ ] Security, consent, audit and FFI boundaries remain intact.
- [ ] Examples, catalogs and documentation match the implementation.
- [ ] Known gaps, rollback steps and follow-up owners are visible.

**Interpretation rule:** this standard improves project stewardship. It does not grant new execution permissions, make untrusted extensions safe, certify language conformance or turn roadmap items into implemented features.
