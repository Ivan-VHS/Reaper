# Reaper VS Code syntax support

> **Documentation review:** 2026-11-27 UTC · syntax-only editor package

[Main Reaper README](../../README.md) · [IDE contract](../../docs/REAPER_IDE.md) · [Feature and maturity matrix](../../docs/FEATURES.md)

**Scope:** syntax-only editor presentation for `.rpr` and `.most` files. This folder registers the languages and provides bracket matching, comments, strings, indentation and TextMate syntax coloring. It does not ship a parser or runtime.

## Install and inspect

Open this folder as an extension-development folder in VS Code. Review the checked-in `package.json` and grammar configuration before packaging. No Marketplace publication is claimed.

## Feature boundary

| Surface | Available here | Not included here |
|---|---|---|
| Language registration | `.rpr` and `.most` | Runtime execution |
| Syntax presentation | Comments, strings, brackets, indentation and TextMate grammar | Semantic AST or project-wide type analysis |
| Runtime language tools | Separate Reaper stdio services | Automatically activated extension client |

## Related Reaper services

The main Reaper package exposes local stdio services:

- `reaper-lsp` — document-local diagnostics, completion, hover, symbols, lexical navigation and formatting in the implemented subset.
- `reaper-dap` — the implemented line-breakpoint and statement-step subset.

These services are not packaged as a VS Code client in this folder and are not activated automatically by this syntax package. Do not claim cross-file type inference, AST refactoring, conditional breakpoints, expression evaluation, profiling or full native C17 parity.

## Security and accessibility

Syntax highlighting grants no runtime, hardware or driver permissions. Keep grammar rules aligned with the canonical language contract, preserve keyboard and theme accessibility, and do not execute project files as part of syntax presentation.

**Maintainer rule:** source, extension manifest and tests define the actual extension surface; roadmap entries do not expand it.
