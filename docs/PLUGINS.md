# Reaper plugin platform

Reaper exposes its 18 first-party products as built-in plugins and supports discovery of local third-party Python extensions through the versioned `ivan-vhs.plugin.v1` manifest contract.

## Host capabilities

| Capability | Implementation |
|---|---|
| Built-in registry | 18 first-party plugins backed by approved product services |
| Stable identity | lowercase kebab-case IDs, semantic plugin versions |
| Manifest discovery | `plugin.json` discovery; metadata only, no code execution |
| Compatibility | plugin API version 1 and host ID `reaper` |
| Lifecycle | explicit load, `on_load`, `run`, `on_event` and `on_unload` hooks |
| Trust boundary | external Python modules require an explicit `trusted=True` decision |
| Validation | bounded manifest size, package-local entrypoint paths, unique IDs, JSON-compatible results |
| Host surface | small `PluginHostAPI` with context and structured logging |
| Diagnostics | enabled/loaded status and manifest discovery errors |

## Quick start

List built-ins:

```sh
python -m reaper --plugins
```

Discover a directory without executing extension code:

```sh
python -m reaper --plugins --plugin-dir ./extensions
```

Run a reviewed extension. The trust switch is intentionally explicit:

```sh
python -m reaper --run-plugin hello-world --plugin-dir ./examples/plugins --trust-plugin --plugin-args '{"message":"Hello"}'
```

Programmatic usage:

```python
from reaper.plugins import PluginManager

host = PluginManager(plugin_dirs=["./extensions"])
plugin = host.get_plugin("hello-world")
host.set_enabled(plugin.plugin_id, True)
host.load(plugin.plugin_id, trusted=True)  # imports reviewed local Python code
result = host.run(plugin.plugin_id, message="Hello")
host.emit("project_saved", {"project": "demo"})
host.unload(plugin.plugin_id)
```

An extension module exports `create_plugin(host_api)`; the factory returns an object with `run(operation, arguments)`. Optional `on_load(context)`, `on_event(event, payload)` and `on_unload(context)` methods implement lifecycle and event hooks. Results and event payloads must be JSON serializable.

## Manifest contract

The canonical JSON Schema is `schemas/ivan-vhs.plugin.v1.schema.json`. The minimal working package is `examples/plugins/hello-world/`. The schema requires a stable ID, SemVer version, host ID, API version, declared capabilities and a package-relative entrypoint.

## Security model

Discovery never imports code. External Python extensions are trusted code: once loaded, they execute in the Reaper process with the user's normal operating-system privileges. `trusted=True` is an explicit acknowledgement, not a sandbox. Do not load unknown or unreviewed packages. The current host does not claim cryptographic publisher verification, permission-enforced filesystem/network isolation, out-of-process crash containment, native C ABI loading, or automatic marketplace installation.

The host rejects path traversal in entrypoints and oversized manifests, but package review and operating-system security remain necessary. Built-in product handlers keep their existing bounded service contracts.

## Compatibility and migration

Plugin IDs are stable. Plugin API major version 1 is the current contract. Additive manifest fields require a schema revision before becoming mandatory; incompatible host API changes require a new major API version and migration notes. Unknown API versions are rejected rather than guessed.

The Python runtime is the reference implementation. The native C17 track does not claim plugin-host parity.
