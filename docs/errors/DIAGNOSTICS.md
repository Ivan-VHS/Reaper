# Reaper diagnostic registry

The CLI and language server share stable `RPR-` diagnostic codes. Codes identify problem classes; wording can improve, but a retired code is never reassigned.

| Code | Severity | Meaning |
|---|---|---|
| RPR-E0000 | error | Unclassified Reaper error |
| RPR-E0001 | error | Invalid source character or token |
| RPR-E0013 | error | Invalid Reaper syntax |
| RPR-E0014 | error | Unexpected closing delimiter |
| RPR-E0100 | error | Runtime operation rejected |
| RPR-E0101 | error | Execution budget exceeded |
| RPR-E0110 | error | MAZA foundation operation failed |
| RPR-W0001 | warning | Incomplete delimiter while editing |

Run `python -m reaper --explain RPR-E0013` for causes and repair guidance. CLI JSON errors include the code, file, one-character source range and suggested next step. The language server publishes the same code and includes the suggestion in diagnostic `data.help`.

Ranges are zero-based UTF-16 positions to match the Language Server Protocol. Suggestions are guidance only; Reaper never edits source automatically.
