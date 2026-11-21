# Reaper internal product ecosystem

**Registry:** `reaper.internal-products.v1` · **Products:** 18 · **Runtime:** shared Reaper process.

The products are native internal modules and services within Reaper—not 18 separate applications or competing runtimes. They share the existing language/runtime, project model and repository contracts.

## Product map

| Product | Responsibility | Executable service |
|---|---|---|
| Operandu | Data, values and logic | Safe value/schema inspection |
| Dropaul | Actions, workflows and process routing | Dependency graph validation and dry-run ordering |
| Zdoro | Integrity and diagnostics | Workspace baseline inspection |
| Pyemont | Development and project construction | Source/project inventory |
| Dilly | Interface and UX | Design-token lint |
| Baplap | Data infrastructure | Deterministic file catalog and SHA-256 fingerprints |
| Sretuo | Quality engineering | Test discovery and planning |
| Kali | Security | Static secret-pattern scan |
| Zalam | Connectivity and integration | Versioned contract validation |
| Liur | Resource management | Repository size and largest-file metrics |
| Keel Koh | Knowledge | Documentation headings and link index |
| Vorof | Reverse engineering | Read-only Python AST structure inspection |
| Vprof | Profiling | Static source and complexity metrics |
| Profe | Standards | Python syntax/convention baseline |
| Prossee | Project intelligence | Task dependency planning |
| Vprossee | Verification | Evidence completeness checks |
| Professiya | Learning | Structured contributor learning paths |
| Profevo | Architecture evolution | Compatibility-aware migration proposals |

## Shared architecture

- **One Reaper Core:** products execute as internal services in the existing Reaper process.
- **Explicit contracts:** stable product names, bounded input validation and named operations.
- **Dropaul:** validates workflow dependencies and returns a deterministic dry-run order. It does not execute arbitrary commands.
- **Kali:** static pattern checks only; no claim of complete security certification.
- **Baplap / Zalam:** local metadata indexing and integration-contract validation remain separate.
- **Sretuo / Vprossee:** test discovery and evidence completeness are separate from actually executing or certifying tests.
- **Liur / Vprof / Zdoro:** repository metrics, static profiling and workspace health are distinct services.
- **Vorof:** parses source into an AST; imported code is never executed.

## Usage

```python
from reaper.products import get_product, list_products, run_product

assert len(list_products()) == 18
print(get_product("Dropaul"))

plan = run_product(
    "Dropaul",
    "plan_workflow",
    steps=[
        {"id": "compile", "depends_on": []},
        {"id": "test", "depends_on": ["compile"]},
        {"id": "package", "depends_on": ["test"]},
    ],
)
assert plan["execution_order"] == ["compile", "test", "package"]
assert plan["dry_run"] is True
```

CLI:

- `python -m reaper.products --list`
- `python -m reaper.products --describe Dropaul`
- `python -m reaper.products --run Dropaul plan_workflow --input '{"steps":[]}'`
- Installed command: `reaper-products --list`

## Safety and maturity

The current implementation supplies 18 product contracts and one bounded local service per product. These services are real, callable foundations, not claims that every future domain capability is complete. Filesystem-oriented services inspect project data and do not modify it; source inspection does not execute imported code; workflow planning is dry-run only; external integrations and privileged operations are not performed. Static security scanning is heuristic and must not be treated as a full audit.

Future extensions must reuse Reaper's existing IR, effect, capability, resource, federation and audit interfaces. Product-specific work must remain behind tested contracts and preserve Reaper's language semantics.
