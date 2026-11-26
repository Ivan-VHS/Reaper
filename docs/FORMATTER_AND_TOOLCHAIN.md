# Formatter and local toolchain inventory

## Document formatter

Reaper Studio exposes `textDocument/formatting` through its stdio LSP server. The first formatter deliberately has a narrow contract:

- It tokenizes the open source document with Reaper's own lexer.
- It normalizes leading indentation from brace nesting, trailing whitespace and the final newline.
- It leaves tokens, comments and string contents in their original order.
- It refuses documents larger than 2 MiB and block nesting deeper than 128 levels.
- It returns one UTF-16-coordinate full-document edit, as required by LSP.

This is a formatting baseline, not a complete pretty-printer. It does not reorder imports, change expressions, infer types or rewrite syntax.

## Toolchain inventory

The `reaper-toolchain` command uses PATH lookup to discover likely compilers, builders, parsers, formatters, debuggers and WASM runtimes. It records paths, but does not run `--version`, inspect process memory or launch any discovered tool.

Create a local inventory:

```sh
reaper-toolchain --output toolchain-inventory.json
```

Create a SHA-256 lock of the binaries found on the current PATH:

```sh
reaper-toolchain --lock toolchain-lock.json
```

Verify the lock later, using the same PATH environment:

```sh
reaper-toolchain --verify-lock toolchain-lock.json
```

A changed path, missing executable or changed file content is reported as a mismatch. A lock describes a local toolchain snapshot; it does not prove the tool is trustworthy, licensed for a particular use or reproducibly built. Review the executable's provenance and licence terms separately before using it.
