# Branches, pushes and pull requests

I use [`.github/merge-operations.json`](./merge-operations.json) to map the English and Russian commands I give the repository operator. This file explains what those commands mean and what must happen before anything is merged.

## What the commands mean

- **Merge** — merge a reviewed pull request into its target branch.
- **Integrate** — bring a change into the project after checking its dependencies and compatibility.
- **Push** — publish commits to the requested feature branch or another approved ref.
- **Force** — mark the work as a priority. It never means skipping review, CI, security checks or branch protection.
- **Execute / Apply** — start the operation after its scope and checks are clear. These words do not authorize extra repositories or branches.

The registry accepts ordinary English and Russian phrases. A longer phrase can map to more than one action; for example, **«Протолкнуть изменения»** means push and integrate. Each action runs once, even when the request contains several synonyms for it.

## Before a merge

I expect the operator to:

1. Check the repositories and branches named in the request, including the current target-branch heads.
2. Read the diffs and look for duplicate work, stale branches, conflicts and dependencies on other repositories.
3. Make changes on a feature branch and keep the pull request focused enough to review.
4. Run the tests, CI and security checks required by that repository.
5. Get the required review, then merge using a method allowed by the repository.
6. Check the resulting commit and make sure dependent projects still point to the right version.

A request to merge is not permission to merge every open PR. Only changes inside the stated scope are candidates.

## Force-push and protected branches

`main`, `master` and `release/*` are protected targets. Do not push to them directly, and do not use force to get around a failed check, a missing review or a branch rule.

Force-push is off by default. I will consider `--force-with-lease` only for a specifically named feature branch, after reading its current remote SHA, checking which commits would be lost and creating a recovery ref. The lease must use that exact SHA.

## GitHub access and audit

The assistant itself is not a GitHub user and cannot approve its own changes as a CODEOWNER. Any unattended automation must use a GitHub App or service account with the minimum permissions needed. It must not have ruleset-bypass permissions.

For each merge, keep a short record of the PR, source and target refs, checks, review, merge method, resulting SHA and outcome.
