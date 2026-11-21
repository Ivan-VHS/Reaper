# Distributed resilience and trust

Reaper is currently a local language/runtime and tooling project. This is an engineering policy, not proof of a distributed runtime.

| Control | Rule |
|---|---|
| Trust | default deny; validate and authorize untrusted input |
| Network | offline operation; verified/allowlisted artifacts only |
| Resource limits | bound steps, queues, imports, payloads and retries |
| Retry | finite attempts, exponential backoff and jitter |
| Failure | fail closed; safe degraded mode |
| Audit | structured evidence, secret redaction |
| Migration | versioned schemas and tested rollback |
| Authority | privileged/destructive operations require human approval |

Do not add a cluster, global coordinator or consensus system to the local interpreter without a concrete requirement.
