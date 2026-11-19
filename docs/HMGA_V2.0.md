# HMGA v2.0 — Reaper repository contract

Status: adopted as a governed engineering standard.

## 1. Exact specification constants

| Symbol | Exact decimal value |
|---|---:|
| N_global | 66666666666666 |
| N_sub | 6454684531153413 |
| F_base | 654684676534 |
| M_mult | 646846453 |
| R_base | 54654654 |

These values are exact declarative metadata, never executable loop bounds, collection sizes, task counts or network retry counts. R_base^(k*k) is symbolic only. Materializing those attempts or generated functions is neither finite engineering work nor a meaningful quality metric.

## 2. Bounded recursive improvement

Each Reaper improvement follows an evidence-backed cycle:

1. Inventory lexer, parser, runtime, CLI, system contracts, examples, tests and CI.
2. Identify one concrete semantic, diagnostic, resource-safety, portability or performance gap.
3. Define expected behavior, non-goals, acceptance tests and rollback.
4. Implement on a feature branch with minimal coupling.
5. Run compileall, unittest, example validation and example execution on supported Python versions.
6. Compare behavior and benchmarks using fixed workloads and recorded platform details.
7. Open a pull request containing implementation and evidence.
8. Merge only after checks and independent human review.
9. Feed test failures and review findings into the next bounded cycle.
10. Modify the improvement process only through its own tests and review.

## 3. Function lineage and composition

Git history and PR metadata are inputs for review, not executable source. The audit records only refs and commits available in the current checkout; a shallow clone does not represent the entire remote history. Historical code must be inspected before reuse.

New functionality needs distinct semantics, a stable public contract, source-aware diagnostics, bounded resource use and positive/negative tests. Candidate combinations use only relevant, existing language/runtime components. Deduplicate by behavior and stable identity; multiplying names or copying functions does not create capability.

Execution-step, call-depth, collection-size and text-length limits remain mandatory. No generated program or repository automation may silently obtain filesystem, network, subprocess or privileged host access.

## 4. Safe delivery

- Use a dedicated feature branch and pull request; do not write directly to main.
- Preserve rulesets, protected paths, tests and CI configuration.
- Retry transient API/network failures only, with a finite cap. Do not retry authorization failures, validation failures or merge conflicts indefinitely.
- Never force-push, rewrite shared history, self-approve, skip a failing test or weaken runtime limits.
- Merge only after relevant CI checks and independent human approval.
- Prefer a small revertible commit and document rollback.

## 5. Reaper-specific quality gates

- Preserve Python support floor 3.10+ and test the configured version matrix.
- Run python -m compileall -q reaper tests tools.
- Run python -m unittest discover -s tests -v.
- Validate and execute checked-in .rpr examples.
- Test successful behavior and deterministic failure paths, including execution, call-depth, collection and text limits.
- Do not claim a compiler, distributed runtime, optimizer or sandbox until implementation and conformance tests exist.

## 6. Audit and definition of done

Run: python tools/hmga_audit.py --strict

The audit is read-only: it reports HEAD, branch, working-tree state, refs visible in the checkout, visible commit count, CI workflows and test inventory. In shallow CI checkouts, history counts are partial.

A change is done only when behavior is tested, resource limits remain effective, CI evidence is available, PR limitations are documented and a revert is practical.
