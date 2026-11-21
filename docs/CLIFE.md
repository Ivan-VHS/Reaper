# CLife — REAPER savepoints and recovery

CLife adapts the supplied stasis / snapshot / awakening model to real project lifecycle operations. It does not claim to preserve a human mind or perform physical cryogenics.

## Python project archive

The portable tool snapshots a source tree into a compressed archive with a SHA-256 manifest:

\`\`\`sh
python tools/clife.py snapshot .
python tools/clife.py verify .clife/snapshots/<snapshot>.clife
python tools/clife.py restore .clife/snapshots/<snapshot>.clife --to ../reaper-recovered
python -m unittest discover -s tests -p "test_clife.py" -v
\`\`\`

Restore always creates a new directory; it never overwrites the source tree.

## Cockos REAPER actions

Load the scripts from **Actions → Show action list → ReaScript → Load**. They are in reaper_scripts/clife/.

| Action | Behavior |
|---|---|
| CLife_Snapshot_Project.lua | Saves the active project and copies its .RPP file to .clife/snapshots/ with a manifest |
| CLife_Verify_Latest.lua | Verifies the newest manifest-backed .RPP snapshot |
| CLife_Restore_Latest.lua | Creates a verified *_CLife_Restored_*.rpp copy after explicit confirmation |

The restore action deliberately does **not** overwrite the active project, replace an open file, or automatically reload the recovered copy. Open the new .RPP manually after reviewing it.

The native ReaScripts copy the .RPP project file only. Referenced audio, video and other media are not copied; keep media in a managed project folder or use the Python CLife archive on the complete project directory.

### REAPER checksum boundary

The self-contained Lua scripts use Adler-32 to detect accidental file corruption without an external crypto dependency. Adler-32 is **not** a cryptographic authenticity mechanism. Use the Python CLife tool's SHA-256 manifest when cryptographic content fingerprints are required.

## Fault and recovery policy

- Missing/unsaved project: stop and ask the operator to save first.
- Manifest or size/checksum mismatch: refuse verification and recovery.
- Snapshot restore: create a new project copy; never silently overwrite.
- The scripts do not execute shell commands, launch external processes, load third-party plugins or run in the audio callback.
- File copies are explicit user-triggered actions. The active session remains under REAPER's normal save/undo model.

The proposed 666,666,666-character generator is intentionally not run. A giant pseudocode stream is not a useful or safe substitute for a bounded, verifiable project savepoint.
