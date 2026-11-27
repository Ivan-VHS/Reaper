# Six Reaper applications for DAK

Six independent Reaper-language application foundations live here:

| Product | Responsibility |
|---|---|
| Omni | Unified workspace, registry and service overview |
| Pomni | Notes, tasks, reminders and personal knowledge |
| LoLo | Local communication and consent-aware message queue |
| PePe | File and digital-asset organization |
| Hyper-kinetic Charge | Read-only telemetry and safe performance recommendations |
| Judo | Permission review and security posture reporting |

## Layout

Each product owns its own directory and versioned application contract:

- domain.rpr — pure, deterministic domain and policy functions;
- main.rpr — runnable local demonstration;
- checks.rpr — small PASS/FAIL smoke scenarios;
- application.contract.json — source target, maturity, safety boundaries and planned line budget.

## Source target

The target is 20,000 Reaper source lines per product (120,000 across the six applications). The first increment is deliberately a compact foundation, not padded code. Current source counts must be recorded from the actual files and CI, not guessed from the target.

## Runtime boundaries

This increment does not claim to provide a native DAK GUI, persistent storage, DOM service lifecycle, background tasks, network transport, filesystem indexing, live hardware telemetry, performance tuning, or privilege changes. The application code currently works with deterministic values supplied by the caller.

System effects must be introduced through versioned DOM/DAK host contracts with explicit capabilities, user consent, quotas, diagnostics and failure handling. No application may silently fall back to ambient filesystem, network, process, device or privilege access.

## Validation status

The checks.rpr files are smoke-check scenarios written in Reaper. They have not been executed by the Reaper parser/runtime in this delivery environment. A successful source upload is not compiler, test or product-completeness evidence.
