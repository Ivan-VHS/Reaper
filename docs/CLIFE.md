# CLife — repository checkpoints, guarded reflash and local federation

CLife is a Python reference-runtime utility layer for repository lifecycle work.
It is not a new Reaper language keyword set, a native C17 implementation, a
distributed coordinator, or an automatic code-rewriting agent.

## Safety contract

- Checkpoint creation reads regular files and writes a separate snapshot.
- Checkpoints exclude `.git`, virtual environments, dependency folders, Python
  caches and the CLife checkpoint store itself.
- Symbolic links are rejected rather than followed.
- Each copied file has a SHA-256 digest, size and portable permission mode.
  `manifest.sha256` detects accidental manifest corruption; it is not a
  cryptographic signature or proof of who created the snapshot.
- Restore first verifies the complete checkpoint and writes into a new or
  empty destination. It never overlays a populated working tree.
- Reflash plans contain proposed file contents and the SHA-256 digest of the
  exact base content. Applying a plan rejects stale files before writing,
  creates a checkpoint, and rolls back files already written if a later write
  fails. File replacement is atomic per file, not a global filesystem
  transaction; do not edit the same working tree concurrently during apply.
- Repository registration and audit are local and read-only. Propagation
  requires an explicit list of paths and produces an ordinary reflash plan.
  There is no background synchronization and no execution of repository code.

Default limits are 100,000 files, 16 MiB per file, 512 MiB per checkpoint and
64 MiB of new content per reflash plan.

## Python API

```python
from reaper.clife import (
    apply_reflash_plan,
    create_checkpoint,
    plan_reflash,
    restore_checkpoint,
    verify_checkpoint,
)

snapshot = create_checkpoint("./my-project")
assert verify_checkpoint(snapshot.path).valid

plan = plan_reflash("./my-project", {
    "src/app.rpr": 'emit "updated"\\n',
    "config/clife.json": '{"enabled": true}\\n',
})

# Inspect and persist the plan before applying it.
print(plan.to_json())
result = apply_reflash_plan("./my-project", plan)

# Recovery always targets a separate directory.
restore_checkpoint(result.checkpoint, "./my-project-recovered")
```

Plans can be serialized with `ReflashPlan.to_json()` and loaded with
`ReflashPlan.from_json()`. The loader checks the schema, paths, size limits and
embedded content hashes before the plan can be applied.

## CLI

Create and verify a checkpoint:

```sh
reaper clife checkpoint ./my-project
reaper clife verify ./.reaper/checkpoints/CHECKPOINT_ID
reaper clife restore ./.reaper/checkpoints/CHECKPOINT_ID ./recovered-copy
```

Prepare an explicit set of changed files. The input JSON is a mapping from
repository-relative paths to UTF-8 text:

```json
{
  "src/app.rpr": "emit 7\\n",
  "config/clife.txt": "enabled=true\\n"
}
```

Create the plan, review it, then apply it deliberately:

```sh
reaper clife plan ./my-project updates.json --output change.plan.json
reaper clife apply ./my-project change.plan.json
```

Fingerprint multiple local repositories without modifying them:

```sh
reaper clife audit ./repo-a ./repo-b ./repo-c
```

The Python `RepositoryNetwork` API additionally supports registering two or
more local repositories and building a guarded propagation plan for selected
files. It does not automatically copy or apply that plan.

## Current implementation boundary

| Capability | Status |
|---|---|
| Checkpoint creation and per-file integrity verification | implemented in Python |
| Restore to a new or empty directory | implemented in Python |
| Reflash plan generation and JSON round-trip | implemented in Python |
| Stale-base rejection and rollback after a write failure | implemented in Python |
| Read-only local repository registry and fingerprints | implemented in Python |
| Selected-file propagation as a reviewable plan | implemented in Python |
| New Reaper source-language statements such as `checkpoint {}` or `reflash {}` | not implemented |
| Native C17 parity | not implemented |
| Remote synchronization, automatic patch approval, background repair | intentionally not implemented |

The existing evolution engine remains proposal- and evidence-driven. CLife
does not bypass its human-review requirements, repository branch protection,
security checks or CI gates.
