# PLAGUE — Reaper-native repository evolution foundation

**Version:** 1.0.0  
**Status:** executable reference-runtime policy slice; not an autonomous repository writer

PLAGUE is a software-engineering system for controlled evolution of explicitly entrusted repositories. Its biological vocabulary describes software architecture only. It does not model, analyze, or manipulate biological organisms.

## Software model

| Biological metaphor | Software-engineering meaning | Required evidence |
|---|---|---|
| Host / organism | One repository and its explicitly linked ecosystem | Repository identity, source revision and ownership boundary |
| Genome / plasmids | Versioned modules, schemas, capability packs and build profiles | Immutable version, digest, provenance and compatibility contract |
| Phenotype | A built application, library or deployable artifact | Reproducible build output and target-specific tests |
| Temperature adaptation | Target platform, architecture, ABI and toolchain profile | Exact target tuple and a matching validation run |
| Variation / mutation | A proposed source patch or contract migration | Reviewable diff, bounded path/byte counts and baseline digest |
| Selection | Deterministic proposal assessment and ranking | Stable policy result and recorded evidence references |
| Symbiosis | Versioned cross-repository contracts and adapters | Both sides' schemas, compatibility tests and source pins |
| Immune system | Scope allowlists, validators, security tests, quotas and review gates | Explicit grants and negative tests |
| Reservoir / seed bank | Immutable source revisions, release artifacts and recovery snapshots | Content digest, retention policy and restore test |
| Metabolism | Bounded compute, memory, patch size, file count and execution budget | Measured resource use and enforced quotas |
| Reproduction | A new branch and reviewable pull request | Parent revision, isolated branch and review record |
| Recovery | Revert or restore from a known immutable checkpoint | Rollback artifact and successful recovery test |

The metaphor is intentionally constrained: a repository cannot grant itself new permissions by describing them in a manifest. Capability grants come from the repository owner and the host environment.

## v1 executable slice

The implementation is authored in Reaper source:

- `plague/engine/core.rpr` validates repository profiles and change proposals.
- `plague/engine/evolution.rpr` checks target compatibility, scope grants, change budgets, required assurance gates, risk ceiling and rollback evidence.
- `select_candidate` ranks up to 128 proposals deterministically by expected benefit minus declared risk. Equal scores are ordered by ascending proposal ID.
- `plague/schemas/repository-profile.v1.schema.json` and `plague/schemas/evolution-proposal.v1.schema.json` define the external JSON contracts.
- `plague/examples/evolution_smoke.rpr` exercises eligible, blocked and selected proposals.
- `tests/test_plague_evolution.py` is a host-side test adapter; policy behavior itself remains in `.rpr`.

### Canonical Reaper tuple layouts

Repository profile (11 fields):

1. repository ID
2. platform
3. stack
4. maximum changed paths (1–100)
5. maximum patch bytes (1–1,048,576)
6. granted scopes
7. required gates
8. rollback required
9. approval mode (`manual` or `risk_based`)
10. approval threshold (0–100)
11. maximum risk (0–100)

Evolution proposal (12 fields):

1. proposal ID
2. target platform
3. target stack
4. changed path count (1–100; this is a count cap, not per-path matching)
5. patch byte count (1–1,048,576)
6. requested scopes
7. completed gates
8. rollback available
9. risk (0–100)
10. expected benefit (0–100)
11. evidence references
12. baseline digest

### Assessment results

- `blocked`: malformed input, target mismatch, ungranted scope, exceeded budget, missing gate, missing required rollback, or risk above the profile ceiling.
- `defer`: admissible proposal whose expected benefit does not exceed its risk.
- `review_required`: proposal must receive an explicit human decision.
- `eligible_for_review`: proposal passed the configured policy gates and may be submitted for human review.

The selector accepts at most 128 proposals and resolves equal scores by ascending proposal ID. The supplied scope list is not an authenticated repository grant, and the changed-path count is not a per-path allowlist check. The selector returns a candidate recommendation only. Neither `eligible_for_review` nor `review_required` authorizes a write, merge, deployment or privileged operation.

## Safety and maturity boundary

v1 is deterministic and advisory. It does not enumerate local files, invoke a shell, access a network, load repository code, create branches, write patches, merge pull requests, install packages, probe devices or mutate firmware. Evidence references are opaque identifiers supplied by the caller; v1 does not claim to verify their contents.

The next implementation gates are: canonical repository inventory and provenance; content-addressed snapshots; patch parsing and byte-level manifest validation; sandboxed validation adapters; exact-SHA CI evidence; branch/PR creation behind explicit grants; signed approval records; and tested rollback. Each adapter must have its own limits and negative tests. No adapter is considered implemented merely because its schema exists. The profile evaluator also does not authenticate the grants or match individual changed paths against allow/exclude patterns.

## Acceptance

The v1 source smoke program must execute through the Reaper reference runtime and assert a low-risk candidate, missing-gate rejection, path-budget rejection and deterministic selection. The repository CI result for the exact pull-request head is the authoritative test result.
