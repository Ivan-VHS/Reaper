# PLAGUE architecture

## Purpose

PLAGUE coordinates repository-level engineering work. It is not a blind source rewriter. It must understand the intended product, compare requirements with observable implementation, identify the complete impact area, produce bounded changes and prove the result with tests and runtime evidence.

## Control flow

    delegated repositories
      -> Plagueborn: inventory and onboarding
      -> Plaguecore: policy, task routing and state
      -> Plagionyx: architecture and dependency analysis
      -> Plagorium: requirement coverage and functional gaps
      -> Blightforge: patch generation
      -> Virulith: feature and integration completion
      -> Scourvex: tests and evidence
      -> Pestigon: security and supply-chain review
      -> Maladrix: performance and resilience
      -> Necrovex: migration, recovery and compatibility
      -> Plaguecore: reconcile results and prepare review

This is a dependency-aware workflow, not a fixed linear pipeline. Findings can return work to an earlier specialist. A patch is not accepted merely because it compiles.

## Runtime layers

| Layer | Responsibility | Required invariant |
|---|---|---|
| Delegation registry | Explicit repository and path grants | Empty by default; no implicit discovery grant |
| Repository adapters | Read metadata, trees, blobs and revisions | Read-only unless an apply grant is validated |
| Intelligence graph | Modules, packages, APIs, ABI, formats and peer repos | Every edge has provenance and revision |
| Requirement model | User-visible behavior and acceptance criteria | Planned features are not delivered evidence |
| Planner | Dependency-aware tasks, risk and ordering | Deterministic plan IDs and bounded scope |
| Patch engine | Generate and apply narrowly scoped diffs | Topic branch, base revision and rollback data |
| Verification engine | Declared checks, tests and target-runtime evidence | Failure or missing evidence fails closed |
| Security gate | Path policy, secrets, dependency trust and effect review | No repository content can grant authority |
| Audit/recovery | Immutable operation record and compensating actions | Every write is attributable and recoverable |

## Action policy

The Reaper module plague/engine/policy.rpr implements a small mode-to-action matrix:

- observe: repository metadata/source reads, dependency graph construction, analysis and report production;
- propose: all observe actions plus change planning and patch generation;
- apply: all propose actions plus topic-branch writes, declared checks and pull-request creation;
- all other modes and actions: denied.

The function does not itself authenticate a grant or inspect a path. A future host adapter must validate, in order:

1. a repository grant exists and is unexpired;
2. the requested repository matches the grant exactly;
3. every affected path is within the allowed roots and outside exclusions;
4. the base revision still matches the planned revision;
5. the requested action is permitted by the mode matrix;
6. an operator approval exists for the requested apply operation;
7. a check identifier resolves to a declared, bounded command;
8. an audit record can be written before a side effect begins.

If any step fails, no write or command is started.

## Bounded proposal assessment

The Reaper v1 policy evaluator sits between planning and any future patch adapter. It validates a repository profile and a proposed change, then returns blockers or an advisory status. The profile constrains the platform, stack, maximum 100 changed paths, maximum 1 MiB patch, granted scope names, required assurance gates, rollback requirement, approval mode and risk ceiling. Proposals carry the declared affected-path count, patch size, requested scopes, completed gates, rollback availability, risk, expected benefit, evidence references and baseline digest.

The evaluator rejects malformed inputs, target mismatches, ungranted scope labels, missing gates, exceeded budgets, absent required rollback and risk above the profile ceiling. It defers changes whose declared risk equals or exceeds expected benefit. Otherwise, it returns `review_required` or `eligible_for_review` according to the approval profile. Candidate selection is bounded to 128 proposals and deterministic: highest `expected_benefit - risk` wins; ties use ascending proposal ID.

These profile scopes do not replace repository grants, and evidence references are opaque caller-provided identifiers. Individual paths are not matched against the grant's allow/exclude patterns. The result cannot authorize writes, checks, merges or releases. Those actions remain behind the separate default-deny mode policy and still require future host-side grant, path, approval and audit validation.

## Repository-wide modification model

PLAGUE may eventually modify every eligible file within an explicitly delegated repository, but it must not treat "repository-wide" as "unbounded":

- source, tests, documentation, build configuration and manifests are eligible only when covered by the grant;
- credentials, secret material, Git internals, private keys and deployment credentials remain excluded;
- generated files are changed only through their owning generator or an explicit generated-file policy;
- dependency updates require provenance, version policy, license review and lockfile consistency;
- destructive migrations require a backup/recovery plan and an explicit approval boundary;
- a cross-repository change is a coordinated set of independently reviewable topic branches and pull requests.

## Full-functionality completion

A feature is complete only when its requirement is linked to:

    requirement
      -> implementation location
      -> integration path
      -> positive and negative tests
      -> target-runtime evidence
      -> documented limitations

A registry entry, stub, TODO removal, passing parser check or successful compile is insufficient. Unavailable hardware, platform or service evidence stays Partial or Blocked; it is never inferred.

## Cross-repository graph

Graph nodes include repositories, packages, modules, public APIs, ABI contracts, generated artifacts, tests, build targets and runtime services. Edges record dependency type, version/range, source path, owning repository and inspected revision.

An impact analysis must traverse reverse dependencies before patch creation. The resulting work is grouped into independently reviewable repository changes and tested against the exact contract versions involved.

## Audit record

Every operation record should include:

- stable operation and plan IDs;
- repository identity and base/head revision;
- mode and grant identifier (never the grant secret);
- requested action and normalized affected paths;
- framework/component responsible;
- patch digest and changed-path inventory;
- declared check IDs, exit states and evidence digests;
- timestamps, outcome, rollback reference and reviewer decision.

Secret values, access tokens and private environment contents must never be copied into reports or logs.

## Failure and recovery

PLAGUE uses fail-closed behavior for unknown schemas, stale base revisions, conflicting edits, missing approval, path escapes, undeclared commands, resource-limit exhaustion and incomplete verification.

A failed operation leaves the default branch untouched. Recovery restores the topic branch to the recorded base or creates a compensating commit; it never force-pushes a protected branch.

## Current boundary

The current foundation implements the Reaper action policy, ten-component registry, bounded repository-profile/proposal evaluator, deterministic candidate ranking, smoke fixtures and versioned JSON contracts. Repository adapters, grant authentication, per-path matching, patch generation, command execution, persistence, graph ingestion and autonomous planning remain Planned. The architecture above is the target contract, not a claim that those layers already exist.