# REAPER / MOST editor support

This starter extension provides .most / .rpr language registration, bracket
matching, comments, strings, indentation and TextMate syntax coloring.

Open this directory as a VS Code extension project and use
Developer: Install Extension from Location... or package it with vsce.

## Capability boundary

This is syntax support, not yet a language server or full IDE. Semantic
completion, diagnostics, rename, AST/IR visualization, debugger, profiler,
project explorer and integrated terminal require compiler protocols and
debug/runtime APIs that are not yet implemented. They are not advertised as
working features.
