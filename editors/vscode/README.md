# Reaper VS Code syntax support

This directory contains syntax-only VS Code language support for `.most` and `.rpr` files: language registration, bracket matching, comments, strings, indentation and TextMate syntax coloring.

## Install and inspect

Open `editors/vscode/` as an extension-development folder in VS Code and inspect its checked-in `package.json` and grammar configuration before packaging or publishing. This repository does not currently document a Marketplace publication.

## Related language services

The Reaper runtime separately provides stdio services:

- `python -m reaper lsp` — JSON-RPC language service with local diagnostics, completion, hover, symbols, lexical navigation and formatting.
- `python -m reaper dap` — debugger adapter with the implemented line-breakpoint and statement-step subset.

These are runtime services, not a packaged VS Code client in this syntax folder. They are not automatically activated by this grammar package. LSP analysis is document-local; it does not claim cross-file type inference or AST refactoring. DAP supports only the documented debugging subset.

## Extension boundary

- This folder owns editor presentation only; it does not provide another parser or runtime.
- Do not advertise semantic completion, diagnostics, debugging, profiling or project navigation as features of the syntax package itself.
- Do not imply cross-file semantic indexing, AST refactoring, conditional breakpoints, expression evaluation or full native C17 parity.
- Keep grammar rules aligned with the canonical language contract and preserve keyboard/theme accessibility.
- Editor syntax highlighting grants no runtime, hardware or driver permissions.

See the [main Reaper README](../../README.md), [IDE contract](../../docs/REAPER_IDE.md) and [documentation index](../../docs/README.md).
