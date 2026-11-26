# PLAGUE — Repository Evolution Framework

PLAGUE is a local, Reaper-native framework family for evidence-driven modernization of explicitly delegated repositories. Its intended responsibilities are repository inventory, architecture and dependency analysis, functional-gap detection, code modification, verification, security review, performance work and compatibility recovery.

## First foundation

The initial implementation lives in the top-level plague/ directory and contains:

- the ten-component framework registry;
- the executable Reaper action policy;
- observe / propose / apply capability levels;
- default-deny behavior for unknown actions and modes;
- fixed denials for default-branch writes, merges, releases, secret access, untrusted-script execution and scope expansion;
- repository-target, change-plan and evidence-bundle JSON schemas;
- a Reaper smoke program connected to CI.

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

The registry is not a completion claim. Each component remains Planned until its source, tests, integration and acceptance evidence are present.

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