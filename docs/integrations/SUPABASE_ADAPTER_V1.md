# Supabase Adapter Contract v1

Project: reaper

Status: contract-only

Default: offline-only

This file declares the data this repository may exchange with the optional Ivan-VHS Supabase data plane. It is an allow-list, not a claim that a network client or hosted integration already exists.

## Allowed data domains

- compiler_build_summaries
- diagnostic_aggregates
- package_manifest_metadata
- workspace_preferences

## Explicit exclusions

- source_text
- source_file_contents
- absolute_local_paths
- environment_variables
- access_tokens
- service_role_keys
- unredacted_compiler_logs

## Runtime rules

- Local project data remains authoritative.
- Cloud access is disabled by default and requires an explicit user action.
- No background synchronization, telemetry or silent uploads.
- A client may receive only SUPABASE_URL and a publishable key at runtime.
- A service-role key, database password or signing secret must never enter this repository or a client binary.
- The shared event and artifact envelope IDs are versioned; domain-specific payload schemas remain owned by this repository.
- Do not change the adapter status to local-ci-verified or hosted-verified without corresponding test evidence.
