# MOST implementation status in Reaper

**Branch:** `feat/reaper-most-parser-m1`  
**Baseline:** native C17 lexer + verified semantic IR from `feat/most-semantic-ir`.  
**Status vocabulary:** `implemented` means executable code and tests exist; `specified` means a written contract exists; `planned` means not yet implemented.

## Architecture slices

| Slice | Current state | Evidence / next gate |
|---|---|---|
| C17 build and native lexer | implemented | `src/lexer.c`, `tests/test_lexer.c` |
| MOST lexical vocabulary | implemented | keyword/operator lexer tests; grammar is not implied |
| Russian MOST keyword vocabulary | implemented in native lexer | src/lexer.c and tests/test_lexer.c; full declaration grammar is not implied |
| Russian executable compatibility subset | implemented in Python reference runtime | reaper/lexer.py maps core Russian spellings to existing parser tokens; tests/test_language.py executes a function/loop/conditional sample |
| Russian 66-rule design guidance | specified | docs/MOST_RUSSIAN_66_RULES.md; readability guidance only, not new language features |
| Semantic IR data model | implemented | `include/reaper/ir.h` |
| IR structural verifier | implemented | `src/ir.c`, `tests/test_ir.c` |
| Bounded fixed-point optimizer driver | implemented | `reaper_ir_optimize_fixed_point`; verified pass loop, 64-iteration ceiling, convergence report and idempotence tests |\n| Native C17 evolution evidence gate | implemented | `src/evolution.c`, `include/reaper/evolution.h`, `tests/test_evolution.c`; fail-closed acceptance gates and human approval requirement |\n| Checked i64 constant-folding pass | implemented | `src/optimizer.c`, `include/reaper/optimizer.h`, `tests/test_optimizer.c`; rejects signed overflow and verifies input/output IR |
| Pratt expression parser | implemented | `src/parser.c`, `include/reaper/ast.h` |
| Flat owned AST with source locations | implemented | `ReaperAstNode`; parser acceptance tests |
| Declaration/block grammar | planned | function/module/record declarations, blocks and recovery |
| Name resolution and static type checker | planned | symbol tables, inference, ADT/exhaustiveness tests |
| Separate MOST intent resolver | deprecated / excluded | МОСТ uses exact aliases and the existing REAPER name resolver; no independent dictionary or intent stage |
| Integer AST-to-IR lowering slice | implemented | `src/lower.c`, `include/reaper/lower.h`, `tests/test_lower.c`; integer literals and binary `+` lower to verified IR; unsupported AST kinds fail explicitly |
| Ownership, borrow and region analysis | specified | CFG-based move/borrow checking and negative tests |
| Effect/capability checking | specified | explicit effect rows and denied-capability tests |
| Native code generation | planned | target ABI and executable conformance fixtures |
| WASM/Web Core | specified | WASI/browser host tests and capability boundary |
| Original 147-feature systems registry | specified | `docs/MOST_147_FEATURE_REGISTRY.md`; separate from the additional cognitive/text/data feature proposal set |
| Cognitive 147-function proposal set | architecture input; implementation not claimed | Must be mapped into compiler primitives, deterministic stdlib and optional intelligence services with per-feature acceptance gates |
| 813-feature architecture map | specified | `docs/REAPER_813_FEATURE_ARCHITECTURE.md` |
| Separate MOST bilingual bridge | deprecated / excluded | exact keyword aliases enter the REAPER token stream; no second frontend or resolver |

## Parser M1 contract

The current native parser accepts exactly one REAPER expression and produces a flat, owned AST. It does not yet parse the complete REAPER declaration/block grammar. Russian keyword aliases do not define a separate grammar:
- integer/decimal/string/boolean/null literals and identifiers;
- prefix arithmetic/logical operators;
- arithmetic, comparison, equality, boolean, null-coalescing and flow operators;
- documented precedence and right-associative exponentiation;
- parentheses and a maximum nesting depth of 256;
- source line/column on every node;
- rejects malformed expressions and trailing tokens.

This is an expression-parser milestone, not a complete source parser. Declarations, functions, blocks, patterns, type syntax and name resolution are not implemented. A deliberately limited integer-expression AST-to-IR lowering slice now exists; it is not general typed lowering.

## Canonical IR contract

The current IR slice is backend-neutral and structurally verified:
- nodes are immutable caller-owned records;
- operands refer only to earlier nodes;
- source locations are retained;
- opcode, result type, operand arity, reference bounds and operand types are checked.

The current executable opcode set is deliberately small (integer constant, signed 64-bit addition and return). The new lowering slice supports integer literals and binary `+`, appends a return, preserves source positions and verifies the result. Identifiers, unary operations, decimals, strings, booleans, comparisons, calls and flow expressions are rejected by this lowerer until their types and semantics are implemented. The checked constant folder rejects compile-time signed-i64 overflow; runtime ADD_I64 overflow behavior and native execution remain future gates.

## Architectural invariants

1. REAPER is the only language, parser, semantic model and runtime.
2. МОСТ maps exact Russian keyword spellings to existing REAPER tokens before the same parser.
3. No separate МОСТ parser, AST, type checker, intent resolver, standard library or backend is permitted.
4. No stemming, guessed inflection, synonym lookup or probabilistic meaning selection occurs during compilation.
5. Russian identifiers are ordinary REAPER identifiers and use the existing REAPER name resolver.
6. A feature is implemented only when REAPER semantics, API, tests, documentation and target behavior have acceptance evidence.

## Next acceptance-gated phases

- **M1 continuation:** declarations, blocks, source-span propagation, parser recovery and parser fuzz tests.
- **M2:** complete REAPER grammar and parser; exact Russian aliases enter the same parser.
- **M3:** REAPER name resolution, typed AST, type/effect checking and expansion of lowering to the full typed expression set.
- **M4:** ownership/region analysis, contracts and resource-effect verification.
- **M5:** native code generation and target ABI conformance.
- **M6:** runtime, standard library, WASM and host capabilities.

## Build and test

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Python remains a compatibility oracle until C17 semantic parity is demonstrated. This branch does not remove Python or claim full native interpreter parity.


## MOST Russian frontend boundary

The native C17 lexer classifies the supported Russian REAPER aliases as keyword tokens and provides a canonical-spelling accessor; ordinary Russian names remain identifiers. The Python reference runtime executes a limited Russian compatibility subset by mapping basic keywords to existing REAPER parser token kinds. Both are REAPER implementations. No separate morphology resolver, synonym lookup, MOST AST, type system or backend is intended. The full REAPER declaration grammar, Unicode NFC validation, static type checking and native/WASM code generation remain separate REAPER milestones. The 66-rule readability mapping is in docs/MOST_RUSSIAN_66_RULES.md.
