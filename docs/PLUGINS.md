# REAPER plugin host

REAPER exposes all 18 internal products as built-in plugins through reaper.plugins.PluginManager. Each plugin has a stable kebab-case ID, display name, version, domain, declared capabilities and an approved service entry point. Existing product services remain the execution layer, so metadata is not misrepresented as a new implementation.

## Built-in plugins

| Plugin ID | Display name | Main responsibility |
|---|---|---|
| operandu | Operandu | Typed values and data inspection |
| dropaul | Dropaul | Deterministic workflow planning |
| zdoro | Zdoro | Workspace integrity |
| pyemont | Pyemont | Project and source inventory |
| dilly | Dilly | Interface and design-token checks |
| baplap | Baplap | Local file catalog and fingerprints |
| sretuo | Sretuo | Test discovery and quality planning |
| kali | Kali | Static security hygiene scan |
| zalam | Zalam | Contract and integration validation |
| liur | Liur | Resource measurements |
| keel-koh | Keel Koh | Documentation index |
| vorof | Vorof | Static source reconstruction |
| vprof | Vprof | Static code-shape metrics |
| profe | Profe | Engineering standards |
| prossee | Prossee | Project planning |
| vprossee | Vprossee | Evidence verification |
| professiya | Professiya | Repository-grounded learning paths |
| profevo | Profevo | Compatibility-aware evolution planning |

## CLI

```sh
python -m reaper --plugins
python -m reaper --plugin-info Dropaul
python -m reaper --run-plugin Dropaul --plugin-args '{"steps":[{"id":"build","depends_on":[]},{"id":"test","depends_on":["build"]}]}'
```

The older --products and --product-info commands remain available.

## Python API

```python
from reaper.plugins import PluginManager

host = PluginManager()
host.set_enabled("Kali", False)
result = host.run("Dropaul", steps=[
    {"id": "build", "depends_on": []},
    {"id": "test", "depends_on": ["build"]},
])
```

The host ships built-in plugins only. It does not import arbitrary workspace Python files, download extensions, execute shell commands, or silently mutate projects. Disabling a plugin blocks dispatch without removing its metadata. Plugin state is local to its PluginManager instance.

## Runtime boundary

Handlers retain their documented safety limits. Dropaul only validates a DAG and returns a dry-run order; Kali is a static pattern scan and not a full security audit; static metrics are not runtime profiling. Python is the current reference host. The native C17 language track does not claim plugin parity.
