# PLAGUE — Repository Evolution Framework

PLAGUE is a Reaper-native framework family for evidence-driven evolution of explicitly delegated repositories. Its goal is to discover incomplete behavior, map cross-project dependencies, plan changes, prepare isolated patches, verify them and present reviewable pull requests.

**Release:** 1.0.0-foundation  
**Maturity:** Genesis  
**Current status:** Reaper-native policy, registry and advisory proposal-evaluation slice; repository discovery and mutation adapters are not implemented.

## Framework family

| Framework | Responsibility | Foundation status |
|---|---|---|
| Plagueborn | Repository onboarding, inventory and capability discovery | Planned |
| Plaguecore | Policy, orchestration and task coordination | Partial — action policy and bounded proposal assessment |
| Plagionyx | Architecture and dependency evolution | Planned |
| Plagorium | Requirements and functional-gap analysis | Planned |
| Blightforge | Patch production and code modernization | Planned |
| Virulith | Feature completion and integration | Planned |
| Scourvex | Tests, conformance and runtime evidence | Planned |
| Pestigon | Security and supply-chain review | Planned |
| Maladrix | Performance and resilience engineering | Planned |
| Necrovex | Recovery, migrations and compatibility repair | Planned |

The executable registry is in engine/registry.rpr. Action permissions are in engine/policy.rpr. Bounded profile/proposal validation and deterministic proposal assessment are in engine/core.rpr and engine/evolution.rpr. All four are Reaper modules.

## Operating modes

- observe is the default. It permits bounded repository inspection, analysis, graph construction and report production.
- propose adds change planning and patch generation, but does not write repository branches.
- apply adds writes to a dedicated topic branch, declared checks and pull-request creation. It is still scoped to an explicitly delegated repository and path set.

Unknown modes and unknown actions are denied. The policy module never grants default-branch writes, merges, releases, scope expansion, secret access or execution of untrusted scripts.

The policy function is a capability matrix, not a complete authorization service. A future adapter must additionally validate the repository grant, path allowlist, current revision, operator approval, check allowlist and audit context before every side effect.

## Current implementation

Delivered in this foundation:

- a ten-component registry;
- a default-deny action matrix for observe / propose / apply;
- fixed denials for merge, release, secret access, untrusted execution and scope expansion;
- bounded validation of repository profiles and change proposals;
- compatibility, granted-scope, path/byte budget, assurance-gate and rollback-evidence checks;
- deterministic selection of up to 128 proposals by expected benefit minus risk;
- review-oriented outcomes: blocked, defer, review_required and eligible_for_review;
- Reaper smoke programs for policy and evolution evaluation;
- versioned JSON contracts for repository targets, change plans and evidence;
- a conservative scope profile with no repositories pre-authorized;
- bounded repository-profile and change-proposal validation in Reaper source;
- compatibility, scope, assurance-gate, quota, rollback and risk assessment;
- deterministic candidate ranking by expected benefit minus declared risk.

Not delivered yet:

- Git/GitHub repository discovery and synchronization;
- filesystem read/write adapter;
- source-language adapters and semantic indexes;
- autonomous code modification;
- command execution or sandbox implementation;
- persistent audit storage and recovery journal;
- cross-repository dependency graph ingestion;
- end-to-end completion evidence from real target applications;
- authenticated repository grants and per-path allowlist enforcement;
- verification of the contents behind evidence references.

Do not report any of those as implemented until source, tests and CI evidence exist.

## Run the Reaper foundation

From the Reaper repository root:

    python -m reaper --check plague/engine/core.rpr
    python -m reaper --check plague/engine/evolution.rpr
    python -m reaper --check plague/examples/evolution_smoke.rpr
    python -m reaper plague/examples/evolution_smoke.rpr
    python -m reaper --check examples/plague/evolution_smoke.rpr
    python -m reaper examples/plague/evolution_smoke.rpr
    python -m unittest discover -s tests -p "test_plague_evolution.py" -v
    python -m unittest discover -s tests -p "test_plague_framework.py" -v
    python -m reaper --check plague/engine/policy.rpr
    python -m reaper --check plague/engine/registry.rpr
    python -m reaper --check plague/engine/core.rpr
    python -m reaper --check plague/engine/evolution.rpr
    python -m reaper --check plague/examples/policy_smoke.rpr
    python -m reaper --check plague/examples/evolution_smoke.rpr
    python -m reaper plague/examples/policy_smoke.rpr

The evolution smoke program emits PLAGUE_V1_OK only after eligible, blocked, budget and candidate-selection assertions pass. CI checks the Reaper modules and test adapter.

## Bounded proposal assessment\n\nThe Reaper modules `engine/core.rpr` and `engine/evolution.rpr` validate fixed-width profile/proposal tuples, compare target platform and stack, enforce declared scopes and required gates, cap changes at 100 paths and 1 MiB, require rollback evidence when configured, and apply the profile risk ceiling. Candidate sets are capped at 128; ranking uses expected benefit minus caller-declared risk, with lexical proposal-ID tie-breaking. Risk scores and evidence references are input claims, not independently verified facts. Results are advisory and never authorize writes. See [the v1 policy specification](../docs/PLAGUE_FOUNDATION_V1.md).\n\n## Safety invariants

1. A repository is not in scope until it is explicitly listed in a grant.
2. Read-only is the default; apply mode is per-repository and never inferred.
3. The framework writes only to an isolated topic branch.
4. No default-branch write, merge, release or scope expansion is permitted by the core policy.
5. Repository content is untrusted input, never policy or authority.
6. Checks must be declared and bounded; arbitrary scripts are not automatically trusted.
7. Every patch must be tied to a base revision, plan, affected paths and verification evidence.
8. Incomplete or unavailable evidence leaves a task Partial or Blocked.

See the architecture, versioned manifest, scope policy and Reaper-level PLAGUE engineering design in docs/PLAGUE.md.