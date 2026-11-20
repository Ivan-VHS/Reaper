# Reaper 666-token catalogue

## Contract

The catalogue contains exactly 666 reserved symbolic lexemes in six domains:

| Ordinals | Domain | Entries |
|---|---|---:|
| 001–120 | Memory, buffers, arenas and slices | 120 |
| 121–240 | Streams, pipelines and execution control | 120 |
| 241–360 | Binding, pattern matching and types | 120 |
| 361–480 | Arithmetic, accumulation and shifts | 120 |
| 481–580 | Vectors, metrics and geometry | 100 |
| 581–666 | System hooks, diagnostics, tracing and meta-nodes | 86 |

The lexeme alphabet is exactly `:`, `;`, `[`, `{`, `]`, `}`, `+`, `=`, `_`, `-`, `*`. Each canonical lexeme is three symbols long and contains no digits. A zero-based base-11 encoding of the ordinal produces a stable, collision-free code. The ordinal is metadata and is never part of source text.

## Runtime contract

All 666 entries are currently **reserved catalogue tokens**. The Python reference lexer and native C lexer recognize them; CLI and runtime APIs expose metadata and lookup. Programs can call `token_catalog()`, `token_info(lexeme)` and `token_is_reserved(lexeme)`. Reserved tokens are not silently treated as implemented operators: attempting to use one in an expression raises a parser diagnostic until its operation-specific semantics, type rules, effects and tests are implemented.

This deliberately separates vocabulary registration from executable semantics. A catalogue row is not a claim that its memory, concurrency, diagnostic or mathematical operation is already implemented.

## Commands

```sh
reaper --catalog
reaper --catalog-group memory
reaper --catalog-token ':::'
reaper --check examples/flow.rpr
```

Native C CLI equivalents:

```sh
reaper-c --catalog
reaper-c --catalog-token ':::'
reaper-c --tokens examples/flow.rpr
```

The canonical JSON source is `language/token_catalog.json`. Run `python tools/generate_token_catalog.py` to refresh the packaged Python data and native C table; use `--check` in CI to detect generated-file drift.
