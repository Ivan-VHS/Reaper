# Reaper first-party application suite

The application suite packages 15 bounded, first-party JSON tools with the Reaper reference runtime. Each application is a separate module under `reaper/apps/`, has a manifest entry, and can be invoked from a valid `.rpr` front-end through the `app_run` runtime builtin.

This is a service layer for the current Python reference runtime. It does not claim native C17 compiler parity or introduce new Reaper grammar. The supplied pseudocode used `fn`, `match`, anonymous functions and record literals that are not current Reaper syntax; the `.rpr` front-ends use the implemented `craft`, `make`, `ask`, `read_json`, `app_run` and `write_json` forms.

## Applications

| ID | Purpose | Input |
|---|---|---|
| `telemetry_guard` | Sensor range validation and power derivation | `readings[]` |
| `log_sieve` | Delimited log parsing and 5xx aggregation | `lines[]` |
| `game_tuner` | Thermal/resource profile recommendation | `hardware` |
| `table_cleaner` | SKU, decimal price, quantity and currency normalization | `rows[]` |
| `api_gateway` | Route selection and request-id idempotency decision | `request`, `routes[]`, optional `cache` |
| `secret_patrol` | Credential-pattern scanning and redacted findings | `files[]` with caller-supplied text |
| `latency_probe` | Nearest-rank p50/p95/p99 | `samples_ms[]` |
| `dag_runner` | Stable dependency ordering and cycle detection | `tasks[]` |
| `span_indexer` | Function declaration index from Reaper lexer tokens | `source`, optional `source_id` |
| `ledger_reconcile` | Integer-cent invoice/payment reconciliation | `invoices[]`, `payments[]` |
| `driver_manifest` | Semantic-version update candidates | `devices[]` |
| `most_build` | Artifact metadata and SHA-256 preflight | `artifact` |
| `text_shield` | Explainable spam score and action recommendation | `text`, optional `links` and `banned_phrases` |
| `physics_bench` | Kinetic energy, mechanical work and efficiency | `run` |
| `bf_vm` | Bounded implementation of all eight Brainfuck commands | `code`, optional input and VM limits |

The complete machine-readable registry is `reaper/apps/manifest.json`. Every CLI operation returns JSON. Applications validate input and reject non-finite numeric values or invalid record shapes.

## CLI

From the Reaper repository root:

```sh
python -m reaper apps list
python -m reaper apps describe telemetry_guard
python -m reaper apps run telemetry_guard --input examples/apps/fixtures/telemetry.json
python -m reaper apps run latency_probe --input samples.json --output reports/latency.json
```

Use `--input -` to read a JSON object from stdin and `--output -` to write the JSON result to stdout. Input is limited to 4 MiB; output is limited to 16 MiB. File inputs and outputs must not be symbolic links. File output is written atomically and the destination directory must already exist. Duplicate JSON keys and NaN/Infinity are rejected.

## Running from Reaper source

Each `examples/apps/<app_id>.rpr` front-end asks for an input JSON path and an output JSON path, calls `app_run("<app_id>", payload)`, then writes the result through the runtime's bounded JSON helper:

```sh
python -m reaper --check examples/apps/telemetry_guard.rpr
python -m reaper examples/apps/telemetry_guard.rpr
```

The wrapper is a Reaper program, while the domain handler is a standard-library Python service in the reference runtime. The experimental native C17 subset does not include collection pipelines or these services.

## Runtime and OS boundaries

- Telemetry, log, table, latency, ledger, physics and moderation tools are offline JSON transforms.
- Secret Patrol only scans text included in the request; it does not recursively traverse the host filesystem.
- Game Tuner returns a recommendation and does not alter scheduler, frame rate or device state.
- API Gateway creates a route/idempotency plan and does not listen on sockets or dispatch handlers.
- DAG Runner orders tasks but never executes task callbacks or shell commands.
- Driver Manifest creates a read-only update candidate list; it does not install, enable, unload or sign drivers.
- MOST Build validates artifact metadata; it is not a MOST compiler or release signer.
- Brainfuck VM has bounded tape memory, instruction steps and output.
- `app_run` executes only the registered first-party handler selected by an exact application ID. It does not load plugins or arbitrary Python modules.

## Verification

```sh
python -m unittest tests.test_apps -v
python -m unittest discover -s tests -v
python -m reaper apps list
```

The suite is available through the Python reference runtime. Native C17 and freestanding target parity require separate implementation and differential conformance work.
