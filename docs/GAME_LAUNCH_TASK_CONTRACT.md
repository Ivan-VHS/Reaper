# Reaper game-launch task contract

**Project author/developer:** Ivan-VHS

Reaper accepts the shared `dakos.game-launch-profile.v1` manifest and turns it into a structured external-process task. This keeps the compiler/workbench separate from host process policy while preserving the exact argument vector, working directory, constrained environment and selected Wine runtime.

```sh
python -m reaper.game_launch_contract game-profile.json --output game-task.json
```

The task is declarative: `shell=false`, `process_created=false` and `requires_trusted_host_executor=true`. Reaper does not start the game, evaluate shell strings, alter the environment globally, or claim native Win32/XP emulation. DAKOS remains the host that decides whether the external runtime is installed and whether a launch is permitted.
