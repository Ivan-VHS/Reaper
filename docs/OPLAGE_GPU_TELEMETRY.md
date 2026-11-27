# OPlague GPU telemetry v1 ingestion

Reaper provides a read-only host-side ingestion adapter for the OPlague oplage.gpu-telemetry.v1 artifact.

## Invocation

\`\`\`sh
reaper-oplage-gpu-audit path/to/gpu-telemetry.json --output build/dakos-gpu-normalized.json
\`\`\`

The input path is explicit. The existing bounded JSON reader rejects symlinks, non-regular files, oversized inputs, duplicate object keys and non-finite JSON values. The adapter checks the exact v1 field set, UUID, timezone-aware capture time, provider/mode, read-only control flag, GPU count, sensor types/ranges, memory consistency and canonical SHA-256 payload digest.

## DAKOS normalized record

The output is the fixed-width record consumed by dakos/gpu/oplage_bridge.rpr:

[schema, snapshot_id, captured_at, provider, mode, available, reason, controls_performed, digest_verified, gpu_rows]

Each GPU row preserves name and driver version. JSON null sensor readings become the literal unknown; they are not estimated or converted to zero. An unavailable provider remains unavailable with an empty GPU list and explicit reason.

The capture timestamp is UTC provenance only. DAKOS/Reaper telemetry sampling requires a separate host/kernel monotonic timestamp when converting normalized readings into time-series events.

## Trust and security boundary

The adapter validates a content digest against the canonical received JSON payload. SHA-256 proves payload integrity relative to that digest; it does not authenticate the publisher, code-sign the exporter or attest the OPlague build. A deployment that needs publisher trust must authenticate the file origin or a signed build/source attestation outside this data schema.

The adapter is user-space only. It does not run nvidia-smi, probe hardware, alter clocks, change voltage, control fans, install drivers, write firmware or grant DAKOS device capabilities. It reads and normalizes a supplied artifact only.

## Tests

The tests/test_gpu_telemetry.py suite covers valid mapping, nullable sensors, explicit unavailable state, tamper detection, provider/mode/control rejection, bounds, impossible VRAM counters and explicit file ingestion.
