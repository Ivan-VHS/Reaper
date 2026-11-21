# Clinical Systems Reliability — CSR-120

CSR-120 translates 120 clinical and physiological principles into software reliability concepts. It is an engineering analogy catalogue plus a deterministic telemetry rule engine; it is not a medical product, clinical diagnostic system, or medical advice.

## Included
- 120 versioned principle records (CSR-001 … CSR-120) grouped into eight domains.
- 36 executable telemetry checks for saturation, queue pressure, resource reserve, retries, latency, clock skew, thermal pressure, configuration drift, integrity, alert fatigue and recovery capacity.
- JSON input/output, stdin support, configurable thresholds, severity ordering and machine-readable schema.

The registry is broader than the executable checks: a principle without a corresponding check is a traceable design concept, not a claimed implemented detector.

## Run

    python tools/clinical_systems.py --catalog --pretty
    python tools/clinical_systems.py telemetry.json --pretty
    cat telemetry.json | python tools/clinical_systems.py

Example telemetry.json:

    {
      "metrics": {
        "cpu_utilization": 0.97,
        "available_memory_ratio": 0.08,
        "p99_latency_ms": 1250,
        "error_rate": 0.025,
        "heartbeat_gap_s": 45
      },
      "thresholds": {
        "p99_latency_ms": 800
      }
    }

A finding includes its principle ID, metric, observed value, comparison, threshold, severity and operational recommendation. Exit codes: 0 healthy/catalog, 1 attention or critical findings, 2 invalid input or execution error.

## Domain map

| IDs | Domain | Engineering interpretation |
|---|---|---|
| 001–015 | Transport | Throughput, bottlenecks, pressure, routing and resource delivery |
| 016–030 | Signals | Thresholds, timing, synchronization, feedback and event propagation |
| 031–045 | Homeostasis | Capacity reserves, thermal control, buffers, cleanup and lifecycle balance |
| 046–060 | Defense | Trust boundaries, incident isolation, threat memory and false positives |
| 061–075 | Dosing | Safe operating windows, cumulative effects, tuning and side effects |
| 076–090 | Lifecycle | Configuration drift, runaway processes, integrity and recovery |
| 091–105 | Diagnostics | Detection quality, root cause, change correlation and degraded operation |
| 106–120 | Operator | Alert fatigue, polling, maintenance, human factors and recovery reserve |

## Integration contract

- Input: JSON object with metrics and optional thresholds; flat metric objects are also accepted.
- Output: csr-120/v1 JSON with status, findings, registry/check counts and timestamp.
- Thresholds use the metric key and override defaults for that metric.
- Missing metrics are skipped; malformed/non-finite values are reported or rejected.
- Use as advisory observability. Never auto-disable devices, kill processes, change firmware, or apply irreversible remediation based only on a finding.
- Collect only operational telemetry needed for the relevant service; avoid personal or patient data.
