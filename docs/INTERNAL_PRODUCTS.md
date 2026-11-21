# REAPER Internal Product Ecosystem

**Status:** integrated Python reference services; desktop navigation and CLI entry points are available. The C17 track is not claimed to implement these services.

All products are modules inside the existing `reaper` package. They share the host process, project root, Python reference runtime and test infrastructure; none is a separate application or repository.

## Product registry

| Product | Responsibility | Initial executable service |
|---|---|---|
| Operandu | Data and logic | Bounded value/type inspection |
| **Dropaul** | Actions and workflows | Deterministic DAG validation and dry-run ordering |
| Zdoro | Integrity and diagnostics | Workspace baseline inspection |
| Pyemont | Development | Source/project inventory |
| Dilly | Interface and experience | Design-token consistency lint |
| Baplap | Data infrastructure | Deterministic local file index with SHA-256 |
| Sretuo | Quality engineering | Test discovery and test-plan output |
| Kali | Security | Static secret-pattern scan (not a full audit) |
| Zalam | Connectivity | Versioned contract validation |
| Liur | Resources | Repository size and largest-file metrics |
| Keel Koh | Knowledge | Markdown heading and link index |
| Vorof | Reverse engineering | Static Python AST/symbol/import inspection |
| Vprof | Profiling | Static code-shape metrics, not runtime profiling |
| Profe | Engineering standards | Python parseability baseline |
| Prossee | Project planning | Dependency graph validation and dry-run task order |
| Vprossee | Verification | Requirement/evidence completeness matrix |
| Professiya | Learning | Repository-grounded learning paths |
| Profevo | Evolution | Compatibility-aware migration proposals |

## Use

```sh
python -m reaper --products
python -m reaper --product-info Dropaul
python -m unittest discover -s tests -p 'test_products.py' -v
```

The Studio menu **Внутренние продукты** opens the built-in product registry. Programmatic use:

```python
from reaper.products import list_products, run_product

registry = list_products()
plan = run_product(
    "Dropaul",
    "plan_workflow",
    steps=[
        {"id": "compile", "depends_on": []},
        {"id": "test", "depends_on": ["compile"]},
    ],
)
```

## Safety and implementation boundaries

- Dropaul validates a declarative dependency graph only. It does not execute commands, scripts, shell strings or arbitrary callbacks.
- Product services inspect data or produce plans. They do not silently edit source files, install dependencies, access networks or launch subprocesses.
- Kali is a static pattern scanner and must not be represented as a complete security audit.
- Vorof, Vprof and Liur perform static/repository measurements; they do not claim runtime behavior or live process telemetry.
- Registry metadata describes product ownership and entry points; it is not proof that every roadmap capability is complete.
- All products are Python reference services. Native C17 parity requires separate implementation and conformance tests.
- The canonical workflow product name is **Dropaul**. Pataki and Patakee are retired names and are not accepted aliases.
