# Mixed syntax and locale profiles

Reaper keeps one lexer, parser, AST, type checker and runtime. A source file can
switch its input profile without creating a second language implementation.

## Directives

The default profile is `classic` syntax with English diagnostics. Directives
apply from their own line onward:

```reaper
@use mode=flow locale=en
@use locale=ru mode=flow

@mode classic
@locale uk
@use mode=flow locale=most
```

The long form accepts `mode=classic|flow` and
`locale=en|ru|uk|most` in either order. The short forms accept
`@mode flow`, `@mode=flow`, `@locale uk` and `@locale=uk`.
`most` selects the Russian-language MOST profile while retaining its own
profile identity in token metadata and diagnostics.
Existing Russian keyword aliases remain accepted for backward compatibility.
New Ukrainian keyword aliases are enabled only under `locale=uk`, so common
short identifiers such as `у` and `і` are not newly reserved elsewhere.

Invalid directives fail immediately with a source location. Directive lines
are masked with same-length whitespace before normal parsing, so line,
column and absolute offsets continue to refer to the user's original file.

## Flow composition

The established `::` operator remains available in every profile. In
`flow` mode, `->` and `|>` are additional spellings:

```reaper
@use mode=flow locale=ru
craft double(value) {
    yield value * 2
}

make total := [1, 2, 3]
    -> map(double)
    |> sum

emit total
```

A line-leading pipe token continues the immediately preceding expression.
A bare step such as `-> sum` injects the previous value as the first argument;
a call such as `-> map(double)` injects it before the explicitly written
arguments. The same form works for declarations, assignments, output
expressions and function returns. Inline `value -> operation(args)` and
`value |> operation(args)` are also accepted in flow mode.

In `classic` mode the arrow spellings remain invalid; existing function calls
and the established `::` composition operator are unchanged.

## Source locations and compatibility

Lexer tokens retain half-open `start`/`end` offsets into the original source,
plus the active `syntax_mode` and `locale`. Use
`reaper.source_profile.span_for_token(token, filename)` for token spans and
`span_for_node(node, filename)` for the full range of an AST expression or
statement. Both return `SourceSpan(file, line, col, start, end)`.
Canonical stack-IR instructions also retain the full originating span,
`syntax_mode` and `locale`; the IR verifier rejects malformed source metadata
before a VM consumes the module.

Lexer, syntax and directive errors expose structured `span`, `syntax_mode`
and `locale` properties on `LexError` / `ParseError`, in addition to readable
messages. The
conservative Python type checker localizes its registered `RPR-T0001` through
`RPR-T0009` diagnostics for Russian and Ukrainian profiles while preserving
canonical type names, identifiers, operators and diagnostic codes. Each type
diagnostic also exposes a full source span and the active profile in both its
Python object and serialized diagnostic payload.

This implementation targets Reaper's Python reference lexer, parser, checker
and canonical stack IR. The native C frontend has not yet been migrated to
these source directives and profile metadata.

Columns and offsets count Unicode code points, matching the Python reference
lexer. This is distinct from the UTF-16 code-unit positions used by LSP edits.
The directives do not alter identifier spelling, number parsing, runtime
limits, effects, or the canonical AST. Localized keyword aliases are exact
table entries; no automatic stemming or synonym guessing is performed.
