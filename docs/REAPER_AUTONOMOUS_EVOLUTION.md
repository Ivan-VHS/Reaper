# Reaper evolution policy

Automation may inspect, test, measure and propose isolated changes. Source writes are a separate capability that requires an authenticated host and a reviewable evidence trail.

| Stage | Requirement |
|---|---|
| Observe | repository and CI evidence |
| Diagnose | reproducible gap |
| Propose | hypothesis, bounded plan, risk, benefit and rollback |
| Implement | revision-pinned topic branch |
| Verify | allowlisted checks in an isolated workspace |
| Promote | protected PR and human approval |

## Native transactional apply engine v1

The C17 core exposes a fail-closed engine in:

- `include/reaper/evolution_apply.h`
- `src/evolution_apply.c`

It provides deterministic whole-file replacement patch descriptors pinned to SHA-256, a bounded request contract, required capability declarations and an explicit host callback boundary.

The required transaction sequence is:

1. Verify a host-issued signed repository grant for the repository and topic branch.
2. Verify the exact base Git object and branch.
3. Open a fresh isolated workspace rooted at that immutable revision.
4. Check a signed per-path write scope and resolve every path inside the workspace without symlink/reparse-point escapes.
5. Read source bytes, compare the expected SHA-256, and stage replacements with a second digest check under the host's file-identity lock.
6. Run only pre-registered check IDs in a sandbox with explicit no-network and resource limits.
7. Materialize staged files in the workspace, then create a Git tree/commit and atomically create a new topic branch from the pinned base revision.
8. Append durable audit records. On a post-commit failure, conditionally remove only the ref created by this request; preserve failed rollback records in a durable recovery store.

The C engine itself performs no ambient filesystem, process or network I/O. Each side effect is delegated to the host adapter, which must provide every required capability and callback. A missing capability or callback rejects the request before execution.

## Important implementation boundary

This is the native transaction engine and host ABI contract, not a shipped operating-system adapter. The repository does not yet include a concrete Windows or POSIX Git/workspace host, an OS-level sandbox implementation, or a Reaper-to-native binding for this callback table. Until those adapters exist and are tested against real Git repositories, the engine cannot be used to mutate a real repository. SOMO's `apply` mode therefore remains blocked; `observe` and `propose` remain non-mutating.

The native test host is an in-memory fake used to exercise the transaction state machine. It is not security evidence for a real filesystem, Git implementation or sandbox.

No self-approval, protection bypass, test weakening or fabricated benchmark claims are permitted.
