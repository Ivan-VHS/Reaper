# Ecosystem Cloud Adapter — Reaper

**Adapter:** `reaper` · **Shared contract:** `ivan-vhs.ecosystem-cloud.v1` · **Status:** contract-only

Reaper remains a local-first compiler, language runtime and development workbench. This manifest reserves an opt-in metadata integration; it does not add a Supabase SDK, network effect or remote compilation path.

## Eligible data

Only versioned published-package metadata, Reaper contract metadata and documentation artifacts explicitly selected by the user may be represented in the shared cloud plane. Source files, private modules, credentials, build directories, compiler caches and unreleased source maps remain local.

## Runtime rules

- No network access occurs when Reaper starts or compiles.
- A connected identity is optional and never a prerequisite for language execution.
- Publish/sync begins only after a user action.
- Every event uses a random client-instance UUID and stable event UUID; neither is derived from device hardware.
- Retries are bounded and idempotent. The authoritative source remains the local Reaper project.
- Conflict resolution belongs to Reaper's module/package semantics; do not silently overwrite source or contracts.

## Implementation boundary

This PR adds the adapter contract and regression test only. A transport client is a separate change requiring a supported Reaper-native HTTP/JSON interface, credential-provider design and integration tests against a local Supabase stack. No Python or third-party SDK runtime is introduced here.
