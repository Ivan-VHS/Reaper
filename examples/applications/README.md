# Reaper application suite — 15 executable examples

This directory contains fifteen standalone programs written for the currently executable Reaper reference grammar. Run an individual application from the repository root:

~~~sh
python -m reaper --check examples/applications/telemetry_guard.rpr
python -m reaper examples/applications/telemetry_guard.rpr
~~~

Run all application tests:

~~~sh
python -m unittest discover -s tests -p test_application_examples.py -v
~~~

The executable language uses craft, make, vary, change, yield, emit, when, otherwise, each, loop while, lists, indexing, and the collection-flow operator ::. The applications intentionally use positional list records because the current grammar does not yet implement object/map literals, property access, anonymous functions, or the fn/match syntax shown in the original conceptual sketches.

## Application catalogue

| # | Program | Purpose |
|---:|---|---|
| 1 | telemetry_guard.rpr | Validate sensor shapes and physical limits; split valid and rejected readings |
| 2 | log_sieve.rpr | Parse delimited log lines, detect HTTP 5xx events, count errors per service |
| 3 | game_tuner.rpr | Convert CPU/GPU/thermal/VRAM samples into a deterministic tuning decision |
| 4 | table_cleaner.rpr | Normalize SKU, decimal separators and quantities; reject invalid rows and de-duplicate SKUs |
| 5 | api_gateway.rpr | Validate request records, dispatch routes, and cache responses by request ID |
| 6 | secret_patrol.rpr | Scan text or explicitly opened files for common credential indicators; redact findings |
| 7 | latency_probe.rpr | Calculate nearest-rank p50, p95, p99 and maximum latency |
| 8 | dag_runner.rpr | Detect duplicate task IDs, unresolved dependencies and cycles; return a topological order |
| 9 | span_indexer.rpr | Index simple craft declarations with one-based line and column positions |
| 10 | ledger_reconcile.rpr | Reconcile invoices and payments using integer cents |
| 11 | driver_manifest.rpr | Compare numeric major.minor.patch versions and produce an update plan |
| 12 | most_build.rpr | Validate release metadata using executable Russian Reaper keyword aliases |
| 13 | text_shield.rpr | Score simple spam indicators and return allow/review/block decisions |
| 14 | physics_bench.rpr | Validate physical inputs and calculate kinetic energy and efficiency |
| 15 | bf_vm.rpr | Execute the eight Brainfuck commands on a bounded byte tape |

The source-level manifest is manifest.rpr. Machine-readable catalogue metadata is manifest.json.

## Record contracts

Reaper list records are positional. The source comments specify the exact field order for each module. Important contracts include:

- Telemetry: [id, temperature_c, voltage_v, current_a].
- Gateway request: [request_id, route, payload]; cached response: [request_id, response].
- Payment: [transaction_id, invoice_id, amount_cents]; invoice: [invoice_id, total_cents].
- Device: [hardware_id, name, enabled, installed_version, latest_version, bus_priority].
- Brainfuck input and output use numeric byte arrays, not Unicode text.

All monetary values are integer cents. Version comparison accepts numeric three-part versions. Latency quantiles use the nearest-rank definition.

## Operational boundaries

These examples are complete for their documented contracts, but they do not pretend to provide operating-system services that the language runtime does not expose:

- game_tuner returns a decision record. Applying FPS, power, affinity or scheduler changes requires a separately permissioned host adapter.
- api_gateway implements request validation, dispatch and in-process idempotency. HTTP/IPC listeners, authentication middleware and durable shared storage belong to a host transport/service layer.
- dag_runner validates a dependency graph and returns an execution order. It does not launch arbitrary commands.
- driver_manifest produces a plan only. Driver downloads, signature verification, installation and rollback require a privileged platform service.
- secret_patrol uses explicit text heuristics and deliberately redacts complete matching lines. It is not a general regular-expression engine or a guarantee that every secret format is detected.
- span_indexer recognizes straightforward craft declarations. It is not a full parser-backed source map and does not replace compiler spans.
- MOST uses the currently executable Russian keyword aliases. The unsupported #syntax directive and reserved fn/struct/match syntax are intentionally omitted.
- bf_vm enforces a 256-cell tape boundary and returns numeric output bytes. It does not grant file, network or native-code access.

File reading occurs only when scan_file or index_file is explicitly called. No program starts a network listener, modifies device drivers, invokes FFI, or changes system tuning.

## Quality and compatibility

The examples share Reaper's parser, AST and Python reference runtime. They use bounded collection operations and explicit state changes. Tests execute all fifteen sources and verify representative outputs and failure paths. The native C17 compiler is a separate partial track; this suite does not claim that all examples compile to native code or have Python/C17 parity.
