# REAPER / MOST editor support

This folder provides .most / .rpr language registration, bracket matching,
comments, strings, indentation and TextMate syntax coloring.

## Language tooling

The repository now includes dependency-free stdio protocol services:

- `python -m reaper lsp` — UTF-16 incremental LSP, versioned documents,
  parser/structure diagnostics, completion, hover, symbols and lexical navigation.
- `python -m reaper dap` — DAP launch, line breakpoints, statement-boundary
  stepping, stack and local-variable inspection.

These are protocol services, not yet a packaged VS Code extension client. LSP indexing is per open document; it does not claim cross-file type inference or AST refactoring.
See [REAPER IDE architecture](../../docs/REAPER_IDE.md) for exact capabilities
and maturity boundaries. Do not advertise type inference, incremental semantic
indexing, conditional breakpoints, expression evaluation, step-out, profiling
UI or native C17 language-service parity as implemented.

## Anatidae editor contract

- This package is syntax support only: `.most` / `.rpr` registration, bracket matching, comments, strings, indentation and TextMate coloring. It is not a language server or full IDE.
- Keep editor grammar aligned with the canonical REAPER / МОСТ language contract; the extension must not introduce separate language semantics.
- Do not advertise semantic completion, diagnostics, rename, AST/IR views, debugging, profiling or project navigation until their protocols are implemented and tested.
- Keep syntax cues readable and do not make color the only carrier of meaning. Respect editor keyboard, focus, theme and reduced-motion settings.
- The extension contributes editor presentation only; it does not grant runtime, hardware or driver permissions.

See the [main Reaper documentation](../../README.md), [Anatidae design system](../../docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md), [UI/UX architecture](../../docs/UI_UX_ARCHITECTURE.md) and [human-first governance](../../docs/HUMAN_FIRST_GOVERNANCE.md).
