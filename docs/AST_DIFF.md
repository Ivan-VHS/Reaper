# Structural AST diff

`reaper-ast-diff` compares Reaper source files after parsing them. It reports
structural changes to statements, expressions, operators and literal values;
comments, whitespace and token spelling are ignored by default.

## Run

```sh
python -m pip install -e .
reaper-ast-diff before.rpr after.rpr
reaper-ast-diff before.rpr after.rpr --include-locations
```

The command prints a deterministic JSON report using the
`reaper.ast-diff.v1` schema. Exit status is `0` when the parsed trees match,
`1` when differences are present, and `2` when a file cannot be read or
parsed. The optional location mode treats line and column changes as part of
the comparison.
