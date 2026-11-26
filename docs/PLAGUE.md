# PLAGUE — Repository Evolution Framework

PLAGUE is a local, Reaper-native framework family for evidence-driven modernization of explicitly delegated repositories. Its intended responsibilities are repository inventory, architecture and dependency analysis, functional-gap detection, code modification, verification, security review, performance work and compatibility recovery.

## First foundation

The initial implementation in the top-level `plague/` directory contains:

- the ten-component framework registry;
- a Reaper action policy with `observe / propose / apply` modes;
- default-deny behavior for unknown modes/actions and fixed denials for default-branch writes, merges, releases, secret access, untrusted-script execution and scope expansion;
- versioned repository-target, change-plan and evidence-bundle schemas;
- bounded repository-profile and evolution-proposal validation in Reaper;
- compatibility, requested-scope, assurance-gate, change-size, rollback and risk assessment;
- deterministic ranking of up to 128 candidate proposals;
- separate Reaper smoke programs and host-side test adapters connected to CI.

The current maturity is **Genesis**. Plaguecore is Partial for the action-policy and bounded proposal-assessment slices; the other nine components remain Planned. The foundation does not yet discover repositories, read repository trees, modify files, invoke tools or create pull requests. Its policy function is not a substitute for grant validation or a sandbox.

## Component responsibilities

| Component | Responsibility | Status |
|---|---|---|
| Plagueborn | Repository discovery and onboarding | Planned |
| Plaguecore | Policy, orchestration and scheduling | Partial |
| Plagionyx | Architecture and dependency evolution | Planned |
| Plagorium | Functional requirements and gap analysis | Planned |
| Blightforge | Source patching and modernization | Planned |
| Virulith | Feature completion and integration | Planned |
| Scourvex | Testing and evidence | Planned |
| Pestigon | Security and supply-chain review | Planned |
| Maladrix | Performance and resilience | Planned |
| Necrovex | Recovery and compatibility migrations | Planned |

No framework component is feature-complete.

## Operating modes

- **Observe** is the default. It is intended for bounded repository inspection, analysis, graph construction and report production.
- **Propose** adds change planning and patch preparation, but does not write repository branches.
- **Apply** is designed for writes to a dedicated topic branch, declared checks and pull-request creation. It still requires an explicitly delegated repository and path set.

The Reaper action policy is a capability matrix, not a complete authorization service. Every future side effect must additionally validate the repository grant, path allowlist, current revision, operator approval, check allowlist and audit context.

## Bounded proposal assessment

The Reaper evaluator is implemented in `plague/engine/core.rpr` and `plague/engine/evolution.rpr`. It validates fixed-width repository profiles and change proposals, checks target platform/stack, requested scope labels, required assurance gates, a maximum of 100 changed paths, a maximum patch size of 1 MiB, rollback availability and the profile risk ceiling.

It returns `blocked`, `defer`, `review_required` or `eligible_for_review`. It ranks at most 128 proposals using `expected_benefit - declared_risk`; ties are resolved by ascending proposal ID. This is advisory only: candidate selection does not write source or authorize a merge.

External contracts are `plague/schemas/repository-profile.v1.schema.json` and `plague/schemas/evolution-proposal.v1.schema.json`. The tuple layout and acceptance cases are documented in [the v1 policy specification](PLAGUE_FOUNDATION_V1.md). Risk/benefit scores and evidence references are caller-supplied; their authenticity and contents are not verified. Scope labels are not authenticated grants, and individual paths are not matched against allow/exclude rules.

## Access model

Every repository must receive an explicit grant with repository identity, base branch, allowed paths, excluded paths, mode, expiry and approved check profile. The initial global scope list is empty. A project is not authorized merely because the GitHub account can see it.

- Observe mode reads eligible metadata/source and creates analysis reports.
- Propose mode creates plans and patches but cannot write repository branches.
- Apply mode may write only to a dedicated topic branch, run declared checks and open a reviewable pull request.
- Merges, releases, secret access, scope expansion and arbitrary script execution are denied by the current core policy.

The scope JSON is a policy contract. Path matching, grant authentication, expiry enforcement, approval, sandboxing and side-effect adapters still need an enforcement implementation.

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

Every step must update implementation, tests, contracts, feature matrix and CI together.

See the [framework README](../plague/README.md), [architecture](../plague/ARCHITECTURE.md) and [v1 proposal-assessment specification](PLAGUE_FOUNDATION_V1.md).
