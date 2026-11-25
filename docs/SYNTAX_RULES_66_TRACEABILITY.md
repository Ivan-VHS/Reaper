# Reaper multi-syntax implementation: 66-rule traceability

**Project author/developer:** Ivan-VHS  
**Registry:** `reaper.syntax-registry.v1`

Status meanings:
- **Implemented:** directly supported by a current frontend or validator.
- **Partial:** a documented subset or static diagnostic exists; the full feature is not implied.
- **Guideline:** a human-readable engineering rule; no formatter or compiler diagnostic currently enforces it everywhere.
- **Not implemented:** no current frontend claims the behavior.

| # | Rule | Status and evidence |
|---:|---|---|
| 1 | One statement, one clear thought | Guideline; source remains authored in its selected dialect. |
| 2 | Meaningful identifiers | Guideline; Python/Reaper parsers accept meaningful names but do not score naming quality. |
| 3 | Consistent indentation | Partial; Python's parser enforces its indentation grammar; other frontends use their own block model. |
| 4 | Explicit delimiters and precedence | Implemented; Python AST, Reaper Pratt parser, Lisp reader and pipeline delimiter scanner parse structure explicitly. |
| 5 | Clear literals and types | Partial; literal grammars are explicit; static typing is not common across every frontend. |
| 6 | Named constants instead of magic values | Guideline; no universal constant-style linter. |
| 7 | Readable line wrapping | Guideline; no formatter is imposed on source files. |
| 8 | Predictable parameter ordering | Partial; Python function calls support ordered arguments and named parameters; other dialects follow their own grammar. |
| 9 | Explicit conditional branches | Implemented in Reaper, Python subset and Lisp `if`; Forth conditional words are not included in this subset. |
| 10 | Predictable loops and exit conditions | Partial; Reaper/Python loop support and Brainfuck jump loops; Forth loop words are not yet included. |
| 11 | Symmetric block and delimiter closure | Implemented; Reaper/Python/Lisp parsers and Brainfuck bracket validation reject unclosed structures. |
| 12 | Comments explain why | Guideline; comment quality is not statically judged. |
| 13 | Consistent casing conventions | Guideline; no cross-language renaming policy is enforced. |
| 14 | Clean whitespace and line endings | Partial; source parsers reject malformed delimiters/indentation where grammar requires it; no global formatter. |
| 15 | Pipelines with `|>` / `->` | Implemented in the pipeline frontend. |
| 16 | Expressions return useful values | Partial; Python/Lisp/pipeline/Forth return expression or stack results; Reaper keeps its existing expression/runtime semantics. |
| 17 | Destructuring and unpacking | Partial; Python subset supports tuple/list assignment; other frontends retain their native forms. |
| 18 | Pattern matching | Partial; Python subset supports literal, wildcard, capture, sequence and OR patterns; no exhaustive algebraic matching. |
| 19 | Immutable bindings by default | Partial; Reaper `make` and Forth stack values have their native rules; Python assignment remains mutable. |
| 20 | Narrow local scopes | Partial; Python functions and Lisp `let`/closures create local scopes. |
| 21 | Lambdas and anonymous functions | Implemented in Python subset, pipeline expressions and Lisp `lambda`. |
| 22 | Explicit ok/err and some/none | Not implemented as a shared sum-type syntax across frontends. |
| 23 | Small function composition | Partial; Python functions, Lisp closures and pipeline stages support composition. |
| 24 | Separate pure transformations and I/O | Partial; pipeline stages are transformations; print/display operations are explicit; no effect type system. |
| 25 | Readable method/transformation chains | Implemented for registered pipeline syntax. |
| 26 | Explicit closure boundaries | Partial; Python and Lisp closures capture their frontend environment; no borrow checker. |
| 27 | Consistent collection literals | Partial; Python, Lisp and Reaper retain their respective literal grammars. |
| 28 | Explicit context propagation | Partial; the runtime shares instruction budget and explicit text input; no general trace/context object is propagated. |
| 29 | Explicit boundary type annotations | Partial; safe built-in Python annotations and the existing Reaper type checker. |
| 30 | Dimension/range/invariant control | Partial; execution limits, Brainfuck tape bounds, cell width and Befunge grid limits are explicit. |
| 31 | Behavioral interfaces / duck typing | Partial; Python subset uses runtime callable/sequence behavior; no shared protocol type checker. |
| 32 | Ownership, references and lifetimes | Not implemented by these frontends. |
| 33 | Bit widths, alignment and byte order | Partial; Brainfuck cell widths and byte I/O are explicit; general ABI/layout syntax is not implemented. |
| 34 | Safe casts | Partial; Python subset uses explicit `int`/`float`/etc. built-ins; no universal checked-cast syntax. |
| 35 | Hygienic macros/code generation | Not implemented. |
| 36 | Attributes/decorators/annotations | Partial; Python boundary annotations are accepted; decorators and general metadata attributes are rejected. |
| 37 | Conditional compilation and targets | Not implemented in the multi-syntax frontend layer. |
| 38 | Structured error contracts | Partial; diagnostics carry frontend, source location where available and explicit error text; a common typed error value is not yet a language feature. |
| 39 | Deterministic evaluation | Partial; polyglot blocks execute in source order with one shared instruction budget; Befunge `?` is deterministic. |
| 40 | Explicit unsafe boundaries | Not implemented; Python subset rejects imports and attribute access, but there is no general unsafe type system. |
| 41 | Explicit module import/export | Existing Reaper native language supports import/export; alternate frontends are isolated and have no shared module loader. |
| 42 | Syntax evolution compatibility | Implemented at registry level; stable syntax IDs and explicit subsets keep added frontends separate from the existing `.rpr` grammar. |
| 43 | Minimal symbolic alphabet | Implemented in Brainfuck (only eight command characters execute). |
| 44 | Hidden tape/stack state | Implemented in Brainfuck and Forth frontends. |
| 45 | 2D spatial syntax | Implemented as a bounded Befunge-93 playfield. |
| 46 | Stack-based pipeline | Implemented in Forth with data and return stacks and colon definitions. |
| 47 | Combinators / point-free composition | Partial; pipeline stages can be named functions and Lisp/Python subsets have higher-order functions; SKI combinators are not a dedicated frontend. |
| 48 | Code as data / homoiconicity | Partial; Lisp supports quote, list structures and evaluation; macro expansion is not implemented. |
| 49 | Self-modifying live text | Partial; Befunge-93 `p` writes to its bounded playfield. |
| 50 | Implicit coercion/tolerant dynamic typing | Not implemented as a universal coercion mode; operations retain each frontend's explicit host semantics. |
| 51 | Punctuation and nested delimiters | Implemented in Lisp S-expressions, Python expressions and pipeline chains. |
| 52 | Limited registers/cells | Implemented in Brainfuck's bounded tape and Forth's bounded stack. |
| 53 | Non-linear instruction order | Implemented by Forth word calls, Brainfuck loop jumps and Befunge-93 directional execution. |
| 54 | Dense puzzle-first programs | Supported by the Brainfuck and Befunge frontends; readability is not required by those grammars. |
| 55 | Exactly eight Brainfuck commands | Implemented; all other source characters are ignored by the Brainfuck command stream. |
| 56 | Tape and pointer model | Implemented; default is 30,000 cells, 8-bit wrapping; 8/16/32-bit widths are selectable. |
| 57 | Right pointer movement | Implemented; moving beyond the configured tape is an error. |
| 58 | Left pointer movement | Implemented; moving left of cell zero is an error. |
| 59 | Byte increment and wrap | Implemented; cell arithmetic wraps to the selected unsigned cell width. |
| 60 | Byte decrement and wrap | Implemented; decrement from zero wraps to the selected cell maximum. |
| 61 | Byte output | Implemented; output bytes are decoded as UTF-8 with replacement for invalid sequences. |
| 62 | Byte input and EOF policy | Implemented; UTF-8 input bytes with selectable zero/keep/max EOF behavior. |
| 63 | Opening bracket | Implemented; bracket pairs are precomputed and zero cells jump past the matching close. |
| 64 | Closing bracket | Implemented; non-zero cells jump back to the matching opener. |
| 65 | Balanced brackets | Implemented; unpaired brackets fail during analysis, before execution. |
| 66 | Pointer-clean loops | Partial; analyzer reports a non-zero textual pointer displacement for loop bodies; it is a diagnostic, not a proof of every dynamic pointer invariant. |

## Execution boundaries

A successful syntax check proves that a source fits the documented parser subset. A successful run proves only that the frontend completed under its configured resource limits. Neither result implies conformance with full CPython, ANS Forth, Scheme, a complete Befunge runtime, operating-system ABI behavior or another external language standard.
