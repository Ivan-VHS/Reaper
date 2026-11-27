# CODEX-66 — Reaper Studio IDE capability browser

CODEX-66 is a native Tkinter tool window in Reaper Studio, not a hosted HTML demo. Open it from **Вид → CODEX-66**, the toolbar button, or **Ctrl+Alt+K**. The catalogue contains six groups of eleven entries (IDs 01–66), searchable by number, name, description and status.

## Status contract

| Status | Meaning |
|---|---|
| Реализовано | The behavior exists in Studio/runtime and is wired to a real action or tested view |
| Частично | A useful slice exists, with a documented boundary (for example, local-document rather than cross-file semantics) |
| В плане | Not implemented yet; the catalogue item is a roadmap entry, not an enabled feature |
| Не поддерживается | The current architecture explicitly reports the capability as unavailable, or the proposed security model would be misleading |

A catalogue status is not a feature toggle. It never enables code, starts a process or grants permissions. The JSON export is a versioned metadata snapshot only.

## Native editor assistance

- **Ctrl+Space** opens local REAPER completion for keywords, built-ins and symbols in the open document. This is deterministic language tooling, not cloud AI or a remote model.
- **F12** navigates to a declaration in the current document.
- **Find references** lists and highlights lexical occurrences in the current document.
- **Ctrl+Shift+R** renames lexical occurrences in the current document after explicit confirmation. This is not cross-file semantic refactoring.
- **Ctrl+K** keeps the existing command palette available.

The completion engine reuses `reaper.language_service.LanguageService`; parsing and language semantics remain owned by the canonical REAPER frontend. JavaScript files continue to use NOO TAH rather than REAPER-language completion.

## Capability boundaries

The current catalogue explicitly distinguishes the existing runtime debugger (line breakpoints, stepping, locals and call stack) from unsupported conditional breakpoints, expression evaluation and restart-frame behavior. It also distinguishes the NOO TAH npm/runtime commands from a general-purpose embedded shell.

The current IDE remains a single-document editor. Integrated Git staging/diff, semantic cross-file indexing, cloud AI, collaboration, coverage, multi-cursor editing and an OS-isolated sandbox are not represented as shipped features. Interpreter quotas are resource controls, not an operating-system security boundary.

## Source of truth

The catalogue is defined in `reaper/codex66.py`, shown by `reaper/codex66_ui.py`, and validated by `tests/test_codex66.py`. The existing engineering constitution remains authoritative for IDE acceptance gates; CODEX-66 is a user-facing capability map, not a replacement for that rulebook.
