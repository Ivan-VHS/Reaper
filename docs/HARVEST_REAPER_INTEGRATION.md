# HARVEST — Reaper runtime pack and Jora integration

**Pack:** `harvest.frameworks`  
**Contract:** `harvest.jora.pack.v1`  
**Source runtime:** Reaper reference runtime  
**Current maturity:** authored / statically specified; Reaper runtime execution is not yet certified

## Scope

HARVEST is a source pack of sixteen independent Reaper capability modules:

- VOXTRACE, CYCLEFORGE, CHRONOS, LEXIGRAPH, CLASHGRAPH
- RESURGENCE, CULTUREFIELD, NARRATIVEFORGE, FACTSEAL
- BEATFORGE, FLOWMETRIC, RHYMECORE, ALBUMARCH
- SCENEMAP, LEGACYGRAPH
- HARVEST ENGINE, which composes the fifteen specialist results

The pack also contains nine shared Reaper core modules, a versioned JSON Schema 2020-12 set, a capability registry, a Jora pack manifest and a Reaper conformance program. The specialist domains intentionally consume supplied annotations, evidence and metadata. They do not claim automatic speech recognition, audio DSP, fact discovery or source credibility from absent data.

## Framework API and IR

Every specialist module follows the same public surface:

- `framework_info()` — returns the versioned framework identity and contract references.
- `diagnose(payload)` — returns structured diagnostics for missing, malformed or out-of-range fields.
- `to_ir(payload)` — creates the framework-specific versioned IR envelope.
- `analyze(payload)` — validates, diagnoses and returns the domain result with its IR.

The IR envelope carries its schema ID/version, framework ID, domain IR schema, operation, contract ID, deterministic node ID, payload and source-span slot. A framework-specific schema constrains the domain payload. Diagnostics identify code, severity, framework, field path, expected/actual values and a remediation hint. Invalid input fails closed; unknown fields are not silently reinterpreted as evidence.

The engine accepts the documented per-framework input payloads and a separate `return_cycles` collection. It emits a composite application IR containing one root and typed child nodes for the specialist frameworks. Missing optional specialist input is represented as unavailable rather than manufactured evidence.

## Shared runtime modules

| Module | Responsibility |
|---|---|
| `base.rpr` | common identifiers, limits and small pure helpers |
| `contracts.rpr` | contract/version and payload validation |
| `ir.rpr` | IR envelope construction and identity |
| `diagnostics.rpr` | stable diagnostic records |
| `storage.rpr` | local snapshot log and generation lookup |
| `transactions.rpr` | staged update, commit and rollback transitions |
| `dependency_graph.rpr` | validated graph nodes/edges and sync topological order |
| `jora_adapter.rpr` | selected-framework application plan and composite IR |
| `runtime.rpr` | common orchestration entry points |

The JSON schemas under `harvest/schemas/` are versioned independently from the Reaper language parser. The pack and registry schemas govern the contract data; the specialist input, output and IR schemas govern each framework's boundary.

## Storage and transaction semantics

HARVEST Storage is local-first and uses the existing Reaper host `read_json` and `write_json` effects only when explicitly called. Its logical snapshot identity is `dataset_id@generation`; this is a deterministic identifier, not a cryptographic digest or provenance proof.

A commit appends a new generation with a parent reference. Rollback appends a new snapshot derived from a prior generation; it does not erase the prior record. Transaction states are explicit: open, committed or rolled back. An invalid or already-finished transaction cannot be committed again.

**Concurrency limit:** the host JSON writer provides atomic replacement of one file, not a cross-process lock or compare-and-swap. The current storage contract is single-writer per dataset/path. Concurrent writers must be coordinated by a trusted host before use; the current Reaper runtime does not claim to provide that lock.

Store paths are caller-selected relative paths. Absolute paths, parent traversal, drive prefixes and unsupported separators are rejected by the HARVEST path guard. Callers remain responsible for choosing a trusted writable root. A path check is not a filesystem sandbox.

## Inter-module dependency graph

Nodes carry a stable node ID, framework ID, contract version and maturity. Edges declare endpoints, relation and delivery mode (`sync` or `async`).

- Synchronous dependency edges must form a DAG; topological order is dependency-first.
- Unknown nodes, duplicate IDs, invalid relations and synchronous cycles produce diagnostics.
- Asynchronous feedback edges are retained in the graph but excluded from startup ordering.
- A graph edge describes a declared dependency; it does not grant file, network, audio, device or other host capabilities.

## Jora source-pack integration

Jora registers the sixteen `harvest.*` capability components from `harvest/jora/components.v1.json`. Selecting a specialist adds its declared dependencies; selecting `harvest.engine` resolves the complete specialist closure and the shared `harvest.runtime` dependency.

The source archive is pinned by SHA-256 and stored as sixteen base64 segments. Jora validates segment order, base64, the pinned digest, archive member types and paths, pack identity, manifest fields and the presence of every referenced source/schema file. It writes archive files to the generated staging project manually; it does not call `tar.extract` or `extractall`.

A generated HARVEST application receives:

```text
src/
  main.rpr
  harvest/
    core/
    frameworks/
    schemas/
    registry/
```

The generated `main.rpr` imports the shared Jora adapter and the selected framework modules. Jora parses and statically type-checks every generated `.rpr` file before publishing the project directory. It does not execute the generated source, install it, grant capabilities or mark the product installable. The application manifest and lock file record the archive digest and included framework closure.

The source archive is included both in the repository checkout and in the `reaper.harvest_bundle` Python package data so the same Jora catalogue remains available from a built distribution.

## Build and verification

From the Reaper repository root:

```sh
python -m unittest tests.test_jora -v
python -m unittest discover -s tests -v
python -m reaper --check examples/flow.rpr
python -m reaper --check harvest/core/diagnostics.rpr
python -m reaper --check harvest/core/ir.rpr
python -m reaper tests/harvest_conformance.rpr
python -m reaper jora catalog --json
python -m reaper jora compose --request examples/jora/harvest-chronicle.request.json --json
python -m reaper jora build --request examples/jora/harvest-chronicle.request.json --output ./out/Chronicle --json
```

The Jora regression suite checks catalogue composition, transitive dependency closure, pinned pack integrity, source-bundle schema metadata and generated source materialization. CI also builds a wheel and verifies that all sixteen bundle segments are present in the distribution.

Until the Reaper CI runtime checks pass on the source branch, HARVEST framework code remains `authored_unverified`. Schema validation and archive integrity are not substitutes for Reaper parser/runtime execution, real storage recovery tests or target-application behavior. Native C17 parity is not claimed.
