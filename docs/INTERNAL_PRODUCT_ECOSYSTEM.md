# Reaper internal product ecosystem

**Registry:** `reaper.internal-products.v1` · **Products:** 18 · **Execution boundary:** in-process, explicit registration.

The ecosystem is a set of native Reaper modules sharing one runtime and common contracts—not 18 separately installed applications or independent runtimes. The product names identify responsibility boundaries; typed payloads and explicit handlers define executable behavior.

## Product map

| Product | Responsibility |
|---|---|
| Operandu | Typed data operations, expressions and logic composition |
| Dropaul | Workflow orchestration, process routing and controlled task execution |
| Zdoro | Integrity, diagnostics, consistency and health |
| Pyemont | Development lifecycle, build coordination and developer workflows |
| Dilly | Interface composition, interaction contracts and accessibility |
| Baplap | Data structures, schemas, serialization and storage adapters |
| Sretuo | Test contracts, regression evidence and test adapters |
| Kali | Capability policy, permission checks and security audit |
| Zalam | Typed connectors, events and external-system adapters |
| Liur | Resource budgets, scheduling hints and performance telemetry |
| Keel Koh | Knowledge indexing, reference resolution and provenance |
| Vorof | Read-only reverse engineering and structural inspection |
| Vprof | Profiling, measurements and execution analytics |
| Profe | Standards, conventions and quality rules |
| Prossee | Project state, dependency intelligence and delivery visibility |
| Vprossee | Evidence validation, traceability and release verification |
| Professiya | Learning paths, guided reference and progression |
| Profevo | Architecture models, evolution proposals and compatibility review |

## Shared architecture

- **Reaper Core:** one process/runtime; modules do not create competing interpreters.
- **Contracts:** stable product IDs, JSON-compatible bounded payloads, explicit action names and deterministic registry metadata.
- **Dropaul:** coordinates workflows; it does not bypass Kali policy or invent capabilities.
- **Baplap:** owns schema/data-adapter boundaries; Zalam handles external connector boundaries.
- **Kali:** permissions remain explicit and fail closed; registration does not grant operating-system privileges.
- **Sretuo / Vprossee:** distinguish test execution from evidence verification.
- **Liur / Vprof / Zdoro:** resource observations, profiling and health checks remain separate concerns.
- **Audit:** each successful or failed dispatched handler is recorded in an append-only SHA-256 hash chain.

## Executable API

```python
from reaper.products import ProductRuntime, get_product, list_products

print(get_product("Dropaul"))
print([product.name for product in list_products()])

runtime = ProductRuntime()
runtime.register("dropaul", "plan", lambda payload: {"steps": payload["steps"]})
result = runtime.dispatch("Dropaul", "plan", {"steps": ["check", "build"]})
assert result["steps"] == ["check", "build"]
assert runtime.verify_audit()
```

CLI: `python -m reaper.products --list`, `--describe Dropaul`, `--health`, or `--json`.

## Maturity and safety

This release implements the shared registry, bounded dispatcher, explicit handler registration, deterministic metadata, and hash-chained dispatch audit. Product capability labels are responsibility contracts—not claims that every domain-specific subsystem is complete. A product action without a registered handler fails closed. Payloads are finite JSON data limited to 1 MiB. No external process, network call, package manager, filesystem mutation, privileged operation, or dynamic plugin loading is performed by the dispatcher.

Further product work should land behind each product's contract and tests, using Reaper's existing runtime, IR, effect, capability, resource and federation interfaces rather than duplicating them.
