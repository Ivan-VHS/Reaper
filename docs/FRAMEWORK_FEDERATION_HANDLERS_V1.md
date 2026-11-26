# Reaper Framework Federation — Reaper source handlers v1.1

**Registry:** `reaper.framework-registry/v1`  
**Manifest version:** `1.1.0`  
**Implementation:** twenty importable Reaper modules plus a shared bounded helper module  
**Maturity:** reference-runtime source handlers implemented; native C17 domain handlers and direct compiler bindings remain pending

## 1. What changed

All twenty Framework Federation namespaces now contain six named Reaper `craft` operations matching the six stable operation keys in `language/frameworks.v1.json`: **120 Reaper source handlers** in total.

The common module `examples/frameworks/federation_common.rpr` provides bounded list, pair, identifier, version, and result helpers. Each namespace remains independently importable under `examples/frameworks/modules/`; the implementations are not copied into the registry or C17 host library.

| ID | Namespace | Reaper source operations |
|---:|---|---|
| 001 | CodexNo | `lookup_symbol`, `inspect_feature`, `list_contracts`, `describe_framework`, `compare_versions`, `export_catalog` |
| 002 | Joint Baby | `bind_language`, `validate_abi`, `invoke_foreign`, `marshal_value`, `unmarshal_value`, `release_foreign` |
| 003 | Correpse | `check_invariant`, `reconcile_state`, `compare_contracts`, `validate_schema`, `detect_conflict`, `prove_precondition` |
| 004 | Allocate Purpose | `arena_create`, `arena_reserve`, `arena_release`, `budget_split`, `quota_check`, `allocation_trace` |
| 005 | Collillioi | `map_sequence`, `filter_sequence`, `fold_sequence`, `zip_sequences`, `stable_sort`, `partition_sequence` |
| 006 | Aspdoi | `task_spawn`, `task_cancel`, `await_result`, `deadline_after`, `schedule_task`, `join_scope` |
| 007 | ASJIOP | `abi_negotiate`, `encode_frame`, `decode_frame`, `type_fingerprint`, `call_descriptor`, `validate_layout` |
| 008 | ALLLLL | `feature_lookup`, `feature_enablement`, `enumerate_features`, `dependency_order`, `compatibility_check`, `capability_diff` |
| 009 | Zabor | `grant_create`, `grant_check`, `grant_revoke`, `scope_intersect`, `policy_match`, `audit_decision` |
| 010 | Vjinz | `source_map_lookup`, `span_translate`, `diagnostic_emit`, `trace_register`, `symbol_resolve`, `origin_chain` |
| 011 | SupremeBoy | `quality_gate`, `build_matrix`, `test_evidence`, `regression_compare`, `artifact_attest`, `release_check` |
| 012 | CheeNow | `channel_open`, `channel_send`, `channel_receive`, `channel_close`, `backpressure_check`, `fanout_dispatch` |
| 013 | HumbleBumble | `result_ok`, `result_err`, `map_ok`, `map_err`, `recover_error`, `classify_failure` |
| 014 | Hub2 | `service_register`, `service_resolve`, `endpoint_health`, `event_publish`, `event_subscribe`, `event_ack` |
| 015 | Kloz | `module_load`, `module_export`, `module_import`, `dependency_resolve`, `module_version`, `module_unload` |
| 016 | CO | `core_hash`, `checksum`, `stable_id`, `text_normalize`, `compare_bytes`, `version_parse` |
| 017 | CrippleBO | `fault_record`, `retry_plan`, `circuit_check`, `fallback_select`, `isolate_component`, `recovery_report` |
| 018 | RippleCripple | `stream_open`, `stream_push`, `stream_merge`, `stream_throttle`, `stream_checkpoint`, `stream_close` |
| 019 | Secator | `access_decide`, `principal_resolve`, `secret_ref`, `token_validate`, `policy_compile`, `security_audit` |
| 020 | PollATIA | `stats_snapshot`, `counter_add`, `gauge_set`, `histogram_observe`, `metrics_export`, `privacy_filter` |

## 2. Execution and truth boundaries

The handler functions are Reaper source and are exercised through the current reference interpreter. This increment does **not** claim that the native C17 registry executes these domain operations.

The versioned machine-readable registry reports these distinct counts:

| Capability | Current status |
|---|---:|
| Registered namespaces | 20 |
| Stable operation contracts | 120 |
| Reaper reference-runtime handlers | 120 |
| Built-in native C17 domain handlers | 0 |
| Reaper source bindings to `reaper_framework_invoke` | 0 |

Several operations deliberately return validated plans or descriptors rather than performing privileged work:

- Joint Baby and ASJIOP validate ABI frames and produce call descriptions; they do not load or execute foreign code.
- Aspdoi models task scopes, deadlines and scheduling decisions; it does not introduce an independent operating-system scheduler.
- Zabor and Secator evaluate explicit policy data and create audit/reference records; they do not mint host privileges or retrieve secret material.
- CheeNow and RippleCripple provide bounded local queue/stream state; they are not IPC or network transports.
- Hub2 describes service discovery and event operations; host-owned transport is still required.
- CrippleBO describes circuit, fallback, isolation and recovery decisions; actual process isolation and restart remain host responsibilities.
- PollATIA operates on caller-supplied metric snapshots; it does not export telemetry to a network service.
- CO's rolling fingerprint is explicitly non-cryptographic. It must not be used for signatures, authentication or integrity guarantees.

Every host-side effect must remain behind a reviewed capability-gated adapter. No shell, filesystem, process, network, physical-memory, firmware or device authority is introduced by these Reaper modules.

## 3. Conformance example

`examples/frameworks/federation_handlers_smoke.rpr` imports all twenty namespaces and calls all 120 operations with representative inputs. The wrapper test `tests/test_framework_federation_handlers.py` runs that Reaper source through the repository's existing reference interpreter.

Run:

```sh
python -m reaper --check examples/frameworks/federation_handlers_smoke.rpr
python -m reaper examples/frameworks/federation_handlers_smoke.rpr
python -m unittest tests.test_framework_federation_handlers -v
```

The smoke program is wired into the regular Python 3.10–3.12 CI matrix. The exact PR-head GitHub Actions result remains the authoritative runtime verdict.

## 4. Fifty-thousand-line expansion target

Each of the twenty Federation namespaces has a long-term target of **50,000 qualified production Reaper LOC**. The resulting Federation portfolio target is **1,000,000 qualified production Reaper LOC**.

A line qualifies only when it is first-party executable Reaper source, owned by that namespace, reachable from its public API, non-generated, non-duplicated and covered by conformance tests. Exclude:

- blank lines, comments and documentation;
- tests, examples and fixtures;
- generated registries, schemas and lock files;
- host-language implementation, templates and copied code;
- unreachable code, placeholder branches and duplicated boilerplate.

This first handler increment is an executable foundation, not a claim that any namespace is close to 50,000 lines or feature-complete. The target is not met by source length alone: every namespace also needs typed contracts, diagnostics with `Span`/SourceMap, positive and negative tests, resource bounds, compatibility review, security evidence, CI and native compiler/runtime support before it can be promoted.

## 5. Integration with ДОМ

ДОМ remains Reaper's single foundational application/system runtime. The Federation namespaces stay domain modules, not independent runtimes. Their future adapters must use ДОМ's public ownership boundaries:

- Uu / CO / Collillioi — foundational values and collections;
- Nonconcrete / Joint Baby / ASJIOP / Zabor / Secator — contracts, ABI and capability policy;
- poooVERTY / Allocate Purpose — resource accounting;
- JLOM / Aspdoi / CheeNow / CrippleBO — task, channel and resilience policy;
- System Carriere / Hub2 — service and event communication;
- JennyFlash / RippleCripple — reactive and stream state;
- Establish / Correpse / Kloz / ALLLLL — composition and dependency resolution;
- Vjinz / CodexNo — source provenance, diagnostics and compiler catalogues;
- SupremeBoy / PollATIA — release evidence and privacy-aware metrics.

These are ownership mappings, not permission for a namespace to create a duplicate scheduler, resource ledger, message bus, security authority or runtime lifecycle.
