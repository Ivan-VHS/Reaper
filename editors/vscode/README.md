# REAPER / МОСТ editor support

This directory contains syntax-only VS Code language support for `.most` and `.rpr` files: language registration, bracket matching, comments, strings, indentation and TextMate syntax coloring.

## Separate language and debug protocol services

The Reaper repository also provides dependency-free stdio services:

- `python -m reaper lsp` — UTF-16 incremental LSP, versioned documents, parser/structure diagnostics, completion, hover, symbols and lexical navigation.
- `python -m reaper dap` — DAP launch, line breakpoints, statement-boundary stepping, stack and local-variable inspection.

These are Reaper runtime services, not a packaged VS Code extension client. They are not automatically activated by this syntax package. LSP indexing is per open document; it does not claim cross-file type inference or AST refactoring. DAP supports the documented runtime debugging subset only.

See [REAPER IDE architecture](../../docs/REAPER_IDE.md) for exact capabilities and maturity boundaries.

## Extension boundary

- This package owns editor presentation only. It does not implement a separate language grammar or runtime.
- Do not advertise semantic completion, diagnostics, rename, AST/IR views, debugging, profiling or project navigation as features of this VS Code package.
- Do not advertise type inference, cross-file semantic indexing, conditional breakpoints, expression evaluation, step-out, profiling UI or native C17 language-service parity as implemented.
- Keep editor grammar aligned with the canonical REAPER / МОСТ language contract.
- Keep syntax cues readable and do not make color the only carrier of meaning. Respect keyboard, focus, theme and reduced-motion settings.
- The extension does not grant runtime, hardware or driver permissions.

See the [main Reaper documentation](../../README.md), [Anatidae design system](../../docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md), [UI/UX architecture](../../docs/UI_UX_ARCHITECTURE.md) and [human-first governance](../../docs/HUMAN_FIRST_GOVERNANCE.md).
