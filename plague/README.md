# PLAGUE — Repository Evolution Framework

PLAGUE is a Reaper-native framework family for evidence-driven evolution of explicitly delegated repositories. It is designed to inspect implementation gaps, map cross-project dependencies, plan bounded changes, prepare reviewable patches, verify behavior and coordinate recovery.

**Release:** 1.0.0-foundation  
**Maturity:** Genesis  
**Current status:** ten-component registry and default-deny action policy are present; Plaguecore also has a bounded proposal-assessment slice. Repository discovery, grant enforcement and patch/verification adapters are not implemented.

## Framework family

| Framework | Responsibility | Current status |
|---|---|---|
| Plagueborn | Repository onboarding, inventory and capability discovery | Planned |
| Plaguecore | Policy, orchestration and task coordination | Partial — action policy and proposal assessment |
| Plagionyx | Architecture and dependency evolution | Planned |
| Plagorium | Requirements and functional-gap analysis | Planned |
| Blightforge | Patch production and code modernization | Planned |
| Virulith | Feature completion and integration | Planned |
| Scourvex | Tests, conformance and runtime evidence | Planned |
| Pestigon | Security and supply-chain review | Planned |
| Maladrix | Performance and resilience engineering | Planned |
| Necrovex | Recovery, migrations and compatibility repair | Planned |

The registry is in `engine/registry.rpr`; the mode/action matrix is in `engine/policy.rpr`; bounded proposal validation and assessment are in `engine/core.rpr` and `engine/evolution.rpr`. These are executable Reaper modules.

## Operating modes

- **observe** is the default and is intended for bounded repository inspection, analysis and reporting.
- **propose** adds change planning and patch preparation, but does not write repository branches.
- **apply** is designed for writes to a dedicated topic branch, declared checks and pull-request creation, but only after a repository grant, path allowlist, approval and audit context have been validated by a host adapter.

Unknown modes and actions fail closed. The current policy denies default-branch writes, merges, releases, scope expansion, secret access and untrusted-script execution. The mode/action matrix is not a complete authorization service.

## Delivered foundation

- Ten-component Reaper registry.
- Default-deny `observe / propose / apply` action matrix.
- Fixed denials for merges, releases, secret access, untrusted execution and scope expansion.
- Versioned repository-target, change-plan and evidence contracts.
- Empty-by-default repository authorization in `policies/scope.v1.json`.
- Bounded validation of repository profiles and evolution proposals in Reaper source.
- Target-platform and stack compatibility checks.
- Requested-scope and required-assurance-gate checks against the supplied profile.
- Hard caps of 100 changed paths, 1 MiB per patch and 128 proposals per selection pass.
- Rollback requirement and profile risk-ceiling checks.
- Deterministic selection by expected benefit minus declared risk; equal scores use ascending proposal ID.
- Separate Reaper smoke programs for the action policy and proposal evaluator.

## Proposal assessment v1

The external contracts are `schemas/repository-profile.v1.schema.json` and `schemas/evolution-proposal.v1.schema.json`. The Reaper tuple layouts and assessment states are specified in [the v1 policy document](../docs/PLAGUE_FOUNDATION_V1.md).

The evaluator returns:

- `blocked` for invalid input, incompatible target, ungranted scope label, missing required gate, exceeded size budget, missing required rollback or risk above the profile ceiling.
- `defer` when expected benefit does not exceed declared risk.
- `review_required` when the profile requires manual review or the risk threshold is reached.
- `eligible_for_review` when the proposal clears configured gates and remains below the review threshold.

These results are advisory. Risk and benefit are caller-provided values; evidence references are opaque identifiers. The evaluator does not verify CI artifacts, authenticate a grant, match individual paths against allow/exclude rules or authorize a write.

## Not implemented

- Git/GitHub repository discovery and synchronization.
- Revision-pinned file/tree inventory and cross-repository graph ingestion.
- Grant authentication, expiry enforcement and per-path allow/exclude matching.
- Source-language adapters and semantic indexes.
- Patch generation, conflict handling or filesystem write adapters.
- Sandboxed command execution and verification adapters.
- Persistent audit journal and tested rollback executor.
- Runtime feature-evidence collection and end-to-end completion proof.

A registry entry, schema or smoke example is not evidence that one of these adapters exists.

## Run the foundation

From the Reaper repository root:

```sh
python -m reaper --check plague/engine/policy.rpr
python -m reaper --check plague/engine/registry.rpr
python -m reaper --check plague/engine/core.rpr
python -m reaper --check plague/engine/evolution.rpr
python -m reaper --check plague/examples/policy_smoke.rpr
python -m reaper --check plague/examples/evolution_smoke.rpr
python -m reaper plague/examples/policy_smoke.rpr
python -m reaper plague/examples/evolution_smoke.rpr
python -m unittest discover -s tests -p "test_plague_evolution.py" -v
python -m unittest discover -s tests -p "test_plague_framework.py" -v
```

The evolution smoke program emits `PLAGUE_V1_OK` only after its eligible, blocked, budget and selection assertions pass. CI is the authoritative result for the exact pull-request head.

## Safety invariants

1. A repository is out of scope until an explicit, unexpired owner grant is validated.
2. Read-only is the default; apply mode is never inferred from account visibility.
3. Writes, when later implemented, are limited to isolated topic branches.
4. Default-branch writes, merges, releases and scope expansion remain denied.
5. Repository content is untrusted input and cannot change policy or grant authority.
6. Checks must be declared, allowlisted, bounded and isolated.
7. Every patch must be tied to a base revision, plan, changed-path inventory and verification evidence.
8. Missing or unverifiable evidence leaves a task Partial or Blocked.
9. Every side effect must be attributable and recoverable.

See [the architecture](ARCHITECTURE.md), [the manifest](manifest.v1.json), [the scope policy](policies/scope.v1.json) and [the Reaper-level design](../docs/PLAGUE.md).
