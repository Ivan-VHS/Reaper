# Kora standard-library helpers

Kora provides 66 Python utility functions in seven manifest-backed plugins. It is an optional standard-library extension for Reaper tooling and examples; it does not add a separate runtime or external service.

| Plugin | Domain | Count |
|---|---|---:|
| ZDORO | Math and numbers | 11 |
| DILLY | Strings and text | 11 |
| BAPLAP | Arrays and sequences | 11 |
| KALI | Maps, sets and structures | 11 |
| PYEMONT | Functional flow, async and errors | 11 |
| LIUR | File I/O, environment and reflection | 6 |
| SRETUO | JSON and time | 5 |
| **Total** | | **66** |

## Python API

```python
from reaper.kora import KoraPluginManager, runtime

host = KoraPluginManager()
host.call("num.clamp", 12, 0, 10)  # 10
host.call("str.slugify", "A small example")  # a-small-example
host.call("arr.chunk", [1, 2, 3, 4, 5], 2)
runtime.map.deep_merge({"config": {"enabled": False}}, {"config": {"enabled": True}})
```

The canonical names, plugin ownership and function counts are recorded in `reaper/kora/manifest.json`. Calls go through `reaper.kora.runtime:call`; `KoraPluginManager` enforces per-plugin enable/disable state.

## Validation and build

```sh
python -m unittest tests.test_kora -v
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps --wheel-dir dist
```

Kora uses only the Python standard library at runtime. File and environment operations are explicit function calls; applications remain responsible for choosing trusted paths and handling errors.
