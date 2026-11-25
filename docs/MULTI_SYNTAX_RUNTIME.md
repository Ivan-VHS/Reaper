# Reaper multi-syntax runtime

**Project author/developer:** Ivan-VHS  
**Registry:** `reaper.syntax-registry.v1`  
**Execution result:** `reaper.multi-syntax-result.v1`  
**Polyglot result:** `reaper.polyglot-program.v1`

Reaper keeps its existing native grammar and adds isolated, bounded language frontends behind one registry. Every frontend returns the same result envelope, uses one execution-step budget, and reports its actual dialect identifier.

## Registered frontends

| Syntax ID | Paradigm | Status | Source extensions |
|---|---|---|---|
| `reaper` | Structured, flow-first | Existing native runtime | `.rpr` |
| `python` | Imperative, dynamic | Safe documented subset; not CPython | `.py` |
| `pipeline` | Functional, dataflow | `|>` and `->` chains with bounded operators | `.pipe`, `.ppl` |
| `lisp` | S-expression, homoiconic | Small Lisp with closures, `quote`, `let`, `define`, list operations | `.lisp`, `.lsp`, `.scm` |
| `forth` | Concatenative, stack | Bounded data/return stacks and colon definitions | `.forth`, `.fs` |
| `brainfuck` | Minimal tape machine | All eight classic commands, bracket validation and bounded tape | `.bf`, `.b` |
| `befunge93` | 2D, stack and self-modifying grid | Bounded 80×25 playfield and core Befunge-93 instruction set | `.bf93`, `.befunge` |

The Python frontend deliberately excludes imports, attribute access, file/network access, arbitrary host calls, decorators, classes and code generation. Type annotations are accepted only from a small built-in allowlist. It executes a Reaper-owned AST interpreter; it does not call Python `exec` or `eval`.

The Forth and Lisp frontends implement documented subsets rather than claiming full ANS Forth or a complete Scheme/Common Lisp standard. Befunge uses deterministic direction rotation for `?` so runs are reproducible.

## Run and inspect

List the registry:

```sh
reaper syntax --list
reaper-multisyntax --list --json
```

Validate source without running it:

```sh
reaper syntax --check --syntax python example.py
reaper syntax --check --syntax brainfuck program.bf
reaper syntax --check --polyglot project.polyglot
```

Run an individual source file or override extension detection:

```sh
reaper syntax --syntax forth examples/math.forth
reaper-multisyntax --syntax brainfuck --input "A" examples/program.bf
```

A source can also start with an explicit marker:

```text
#!syntax pipeline
[1, 2, 3, 4] |> map(lambda item: item * 2) |> sum
```

## Polyglot files

A polyglot file is a sequence of explicitly tagged blocks. Each block has its own language state; output is collected in source order. A single global step budget is shared across blocks.

```text
%% python
values = [2, 3, 5]
print(sum(values))

%% forth
4 5 + .

%% lisp
(display (+ 10 20))

%% brainfuck
++++++++[>++++++++<-]>+.
```

Run or validate the complete file:

```sh
reaper syntax --polyglot project.polyglot
reaper syntax --polyglot --check project.polyglot
```

Blocks do not share mutable variables or interpreter heaps. Cross-language value exchange is not implied by the shared output channel. Each block is an isolated frontend execution in source order, not a parallel thread.

## Resource and safety boundaries

- Source and input text are each limited to 1,000,000 characters.
- The default instruction budget is 1,000,000 steps and applies to the complete polyglot run.
- Python collection growth is bounded; Lisp nesting is limited; Forth data and return stacks are bounded.
- Brainfuck defaults to a 30,000-cell tape, 8-bit wrapping cells and EOF-to-zero. Tape size, 8/16/32-bit cell width and EOF policy are explicit options.
- Brainfuck pointer movement outside the tape is an error. Unmatched brackets fail before execution.
- Befunge-93 uses a maximum 80×25 playfield; out-of-grid `p`/`g` accesses fail.
- No frontend invokes a shell, imports arbitrary Python modules, opens files, installs runtimes or accesses the network.

## Architecture

`SPECS` is the single registry. `normalize_syntax` resolves aliases; `detect_syntax` handles extensions and source markers; `validate_source` parses without execution; `run_source` executes one selected frontend; `parse_polyglot` and `run_polyglot` orchestrate source-ordered blocks under one shared budget.

The existing `.rpr` lexer, parser, tree-walk runtime, canonical IR and VM remain unchanged. These frontends do not rewrite native Reaper syntax or silently translate source code into Python. New syntax engines must be registered with a stable ID, documented subset, explicit resource limits, validation tests and traceability against the shared 66-rule checklist.
