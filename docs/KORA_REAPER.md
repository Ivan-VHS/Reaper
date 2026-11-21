# Kora for Cockos REAPER

Kora adds 66 standard functions in seven manifest-backed plugins: ZDORO, DILLY, BAPLAP, KALI, PYEMONT, LIUR and SRETUO. The Python utility API uses only the standard library. The DAW examples are Lua ReaScripts that run in Cockos REAPER's own script host and call the ReaScript API directly.

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

\`\`\`python
from reaper.kora import KoraPluginManager, runtime
host = KoraPluginManager()
host.call("num.clamp", 12, 0, 10)             # 10
host.call("str.slugify", "My REAPER Mix")     # my-reaper-mix
host.call("arr.chunk", [1, 2, 3, 4, 5], 2)
runtime.map.deep_merge({"fx":{"wet":0.5}}, {"fx":{"enabled":True}})
\`\`\`

The canonical names and ownership are in \`reaper/kora/manifest.json\`. All calls use \`reaper.kora.runtime:call\`; plugin enable/disable is enforced by \`KoraPluginManager\`.

## Install and run applications inside REAPER

In Cockos REAPER open **Actions → Show action list → ReaScript → Load**, choose a \`.lua\` script from \`reaper_scripts/kora/\`, then run it from the Action List. A ZIP of the scripts is published by the **Kora REAPER builds** workflow.

- **Track Health Dashboard**: read-only project name, BPM, track counts, mute/solo state and tracks without media.
- **Prefix Selected Tracks**: prompts for a prefix and renames selected tracks in one REAPER undo block.
- **Marker and Region Report**: prints marker and region names/positions to the REAPER ReaScript console.

## Runtime boundary

The Python utility library and Lua ReaScript host are separate runtimes: the Lua applications call native REAPER APIs and do not import Python into Lua. No included application launches Node.js, a shell, a browser, a network request or a separate process. Mutations are explicit and undoable. Timers, async work and file watchers must never run in the audio callback. This package delivers installable ReaScripts and a Python wheel, not compiled VST3/AU/CLAP audio effects.

## Test and build

\`\`\`sh
python -m unittest tests.test_kora tests.test_kora_reascripts -v
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps --wheel-dir dist
\`\`\`
