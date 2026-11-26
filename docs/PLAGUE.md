# PLAGUE — Repository Evolution Framework

PLAGUE is a local, Reaper-native framework family for evidence-driven modernization of explicitly delegated repositories. Its intended responsibilities are repository inventory, architecture and dependency analysis, functional-gap detection, code modification, verification, security review, performance work and compatibility recovery.

## First foundation

The initial implementation lives in the top-level plague/ directory and contains:

- the ten-component framework registry;
- bounded repository-profile and evolution-proposal validation;
- deterministic compatibility, scope, resource-budget, assurance-gate and rollback-evidence assessment;
- risk/benefit candidate ranking for up to 128 proposals;
- the executable Reaper action policy;
- observe / propose / apply capability levels;
- default-deny behavior for unknown actions and modes;
- fixed denials for default-branch writes, merges, releases, secret access, untrusted-script execution and scope expansion;
- repository-target, change-plan and evidence-bundle JSON schemas;
- five JSON contracts covering repository targets, change plans, evidence, repository profiles and evolution proposals;
- two Reaper smoke programs and a host-side test adapter connected to CI.

The current maturity is **Genesis**. The foundation does not yet discover repositories, read repository trees, modify files, invoke tools or create pull requests. Its policy function is not a substitute for grant validation or a sandbox.

## Component responsibilities

| Component | Responsibility |
|---|---|
| Plagueborn | Repository discovery and onboarding |
| Plaguecore | Policy, orchestration and scheduling |
| Plagionyx | Architecture and dependency evolution |
| Plagorium | Functional requirements and gap analysis |
| Blightforge | Source patching and modernization |
| Virulith | Feature completion and integration |
| Scourvex | Testing and evidence |
| Pestigon | Security and supply-chain review |
| Maladrix | Performance and resilience |
| Necrovex | Recovery and compatibility migrations |

Plaguecore is Partial only for its action-policy slice. The other nine components are Planned. No framework component is feature-complete.

## Advisory evolution evaluator

The Reaper core validates bounded repository profiles and change proposals. The evolution evaluator rejects target mismatches, ungranted scopes, exceeded path/byte budgets, missing assurance gates, absent required rollback evidence and risk above the profile ceiling. It returns blocked, defer, review_required or eligible_for_review and ranks up to 128 candidates by expected benefit minus risk. This is advisory only: proposal eligibility never grants write authority, and evidence references are not cryptographically verified in this slice.

See PLAGUE_FOUNDATION_V1.md for tuple layouts and acceptance fixtures.

## Access model

Every repository must receive an explicit grant with a repository identity, base branch, allowed paths, excluded paths, mode, expiry and approved check profile. The initial global scope list is empty. A project is not authorized merely because the GitHub account can see it.

- Observe mode reads eligible metadata/source and creates analysis reports.
- Propose mode creates plans and patches but cannot write repository branches.
- Apply mode may write only to a dedicated topic branch, run declared checks and open a reviewable pull request.
- Merges, releases, secret access, scope expansion and arbitrary script execution are denied by the current policy.

The current JSON scope file describes the intended policy contract. Path matching, grants, expiry, approval, sandboxing and adapters still need an enforcement implementation.

## Full-functionality evidence

A feature is not complete because its name appears in a catalogue or the code contains a function with the expected name. PLAGUE must connect each requirement to implementation, integration, positive and negative tests, target-runtime evidence and documented limitations. Missing evidence leaves the capability Partial or Blocked.

## Engineering sequence

1. Complete delegation, path-scope validation and immutable audit records.
2. Add read-only Git and filesystem adapters with revision-pinned inventories.
3. Build language adapters and the cross-repository ecosystem graph.
4. Add requirement coverage and deterministic dependency-aware plans.
5. Add patch generation and conflict-aware topic-branch writes.
6. Add isolated, allowlisted verification.
7. Integrate security, performance, recovery and compatibility gates.
8. Add coordinated multi-repository pull requests.

Every step must update its implementation, tests, contract, feature matrix and CI together.

See the framework README and architecture in the plague directory.