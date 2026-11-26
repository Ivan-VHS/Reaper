# Reaper Self-Hosting Bootstrap

## Objective

Move language implementation logic into Reaper source files. The finished compiler must be able to compile and rebuild its own source; merely renaming the Python or C implementation does not count as self-hosting.

## Current status — Stage 0 and partial Stage 1

`selfhost/lexer.rpr` is the first executable frontend component implemented in Reaper itself. It performs scanning in Reaper functions and uses only the language's existing string indexing, lists, comparisons, loops, flow-independent control statements and standard collection operations. The Python interpreter is only the bootstrap host that executes this Reaper program.

The stage-0 lexer currently covers ASCII identifiers and digits, keywords, decimal/integer literals, strings and escapes, comments, newlines, punctuation, operators and source positions. It returns a structured error token for an invalid character or malformed string. The Python lexer accepts Unicode identifiers; that compatibility gap is deliberate and must be closed before the self-hosted frontend can replace the reference lexer.

The Python test suite executes the Reaper source and checks its internal assertions. This proves that the lexer logic is running as Reaper code; it does **not** prove a self-hosting compiler or complete frontend parity.

### Stage 1: Pratt expression parser (partial)

`selfhost/parser.rpr` implements a Pratt expression parser in Reaper source. It consumes the token-array shape emitted by the bootstrap lexer and builds compact array-form expression nodes. The implemented expression slice covers literals, names, unary expressions, grouping, list literals, function calls, indexing and infix operators, including `::` and right-associative `**`.

`selfhost/program_parser.rpr` adds a Reaper-written statement parser and a stable array AST shape `[kind, token, value, children]`. It covers declarations and reassignment, functions and parameters, imports/exports, `emit`, `yield`, `when`/`otherwise`, `each`, `loop while`, blocks, expression statements and Pratt expressions. Its embedded assertions cover precedence, source positions, nested branches, iteration, imports/exports and malformed statement boundaries. `tests/test_self_hosting.py` now invokes this source through the reference runtime; CTest already runs that test module when Python is available.

This is still **not** a complete parser replacement. Unicode identifier parity, full token-by-token conformance, exact Python `Node` AST parity, semantic analysis, canonical IR lowering and self-rebuild are not yet established. The Python parser remains the compatibility oracle.

## Bootstrap stages

| Stage | Reaper-written component | Acceptance gate |
|---|---|---|
| 0 | Lexer | Token-by-token parity for the supported language, Unicode and error locations included |
| 1 | Pratt expression parser (partial); statement parser and canonical AST still pending | Calls, indexes, lists and operators are covered; complete AST parity and statement grammar remain the acceptance gate |
| 2 | Semantic analysis and runtime support | Differential conformance against the reference interpreter |
| 3 | Canonical IR construction and verifier | Deterministic IR plus rejection of malformed or unsafe IR |
| 4 | Optimizer passes | Differential semantics, fixed-point budget and reproducible output |
| 5 | Native code-generation frontend | Generated output builds and passes the complete conformance suite |
| 6 | Bootstrap closure | Stage-1 rebuilds Stage-1 reproducibly; clean-room Stage-0/Stage-1/Stage-2 builds agree |

## Non-negotiable rules

1. Reaper implementation logic belongs in `.rpr` sources; host code is limited to bootstrap, platform primitives and test orchestration.
2. Keep the Python implementation as a compatibility oracle until full differential parity is demonstrated.
3. Keep the C17 runtime/compiler track as the native execution substrate during bootstrap; do not claim it is a complete runtime until the full suite passes.
4. Every stage has positive, negative, regression, resource-limit and source-location tests.
5. A stage is not complete because its source file exists. It must pass the stated acceptance gate on a clean checkout.
6. Bootstrap builds must be deterministic and record source hashes, compiler version, target and build inputs.
7. No stage may silently add filesystem, network, process, shell or hardware authority to ordinary Reaper programs.

## Immediate next work

- Close Unicode identifier parity in the self-hosted lexer.
- Expand token conformance to every keyword, operator, escape, whitespace and malformed-source case.
- Close Unicode identifier parity and complete token-by-token lexer conformance.
- Compare the Reaper-written statement AST against the Python `Node` AST over the same golden source corpus.
- Add semantic analysis and canonical IR construction in Reaper after AST parity is demonstrated.
- Define a versioned canonical AST representation and compare parser output with the Python AST over a shared golden corpus.
- Add differential tests for calls, indexes, list literals, operator precedence, nested blocks and malformed statements.
- Move the CLI, diagnostics, semantic analysis and compiler pipeline into Reaper in dependency order.


## Typed records and explicit platform declarations — partial bootstrap

The Reaper-written statement frontend now parses:

- struct declarations of the form: struct Name { field: Type }, with source-aware field nodes;
- platform declarations of the form: platform Name { property := literal };
- inline exports of structure and platform declarations.

selfhost/type_declarations.rpr validates unique record fields and supported scalar field types, validates a platform descriptor against a deliberately small target profile set, and calculates deterministic scalar C-ABI field offsets, record alignment, and final size. The initial layout subset covers fixed-width integers, f32/f64, bool, ptr, usize, and isize.

The initial target descriptor profiles are:

| Target triple | Object format | Calling convention |
|---|---|---|
| x86_64-unknown-linux-gnu | ELF | System V |
| x86_64-pc-windows-msvc | PE/COFF | Win64 |
| aarch64-apple-darwin | Mach-O | AAPCS64 |
| wasm32-unknown-wasi | WebAssembly | wasm32 |
| x86_64-unknown-none-elf | ELF | System V |

This is declaration and scalar-layout validation only. It does not provide cross-compilation, nested-record or array layout, ownership/borrowing, a production type checker, target object emission, or a freestanding runtime. The production reference parser and native AOT backend remain separate compatibility gates.

