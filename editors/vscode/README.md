# REAPER / MOST editor support

This starter extension provides .most / .rpr language registration, bracket
matching, comments, strings, indentation and TextMate syntax coloring.

Open this directory as a VS Code extension project and use
Developer: Install Extension from Location... or package it with vsce.

## Protocol services

- `python -m reaper.lsp` — LSP language workbench with versioned UTF-16 edits and background symbol indexing.
- `python -m reaper.dap` — DAP launch, line breakpoints, statement-boundary stepping, stack and locals.

The protocol services are available for editor-client integration; this folder remains the syntax extension until the VS Code client adapter is wired.

## Capability boundary

This is syntax support, not yet a language server or full IDE. Semantic
completion, diagnostics, rename, AST/IR visualization, debugger, profiler,
project explorer and integrated terminal require compiler protocols and
debug/runtime APIs that are not yet implemented. They are not advertised as
working features.

## Anatidae editor contract

- This package is syntax support only: `.most` / `.rpr` registration, bracket matching, comments, strings, indentation and TextMate coloring. It is not a language server or full IDE.
- Keep editor grammar aligned with the canonical REAPER / МОСТ language contract; the extension must not introduce separate language semantics.
- Do not advertise semantic completion, diagnostics, rename, AST/IR views, debugging, profiling or project navigation until their protocols are implemented and tested.
- Keep syntax cues readable and do not make color the only carrier of meaning. Respect editor keyboard, focus, theme and reduced-motion settings.
- The extension contributes editor presentation only; it does not grant runtime, hardware or driver permissions.

See the [main Reaper documentation](../../README.md), [Anatidae design system](../../docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md), [UI/UX architecture](../../docs/UI_UX_ARCHITECTURE.md) and [human-first governance](../../docs/HUMAN_FIRST_GOVERNANCE.md).
