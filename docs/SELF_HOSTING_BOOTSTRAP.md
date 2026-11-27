# Reaper Self-Hosting Bootstrap

## Objective

Move language implementation logic into Reaper source files. The finished compiler must be able to compile and rebuild its own source; merely renaming the Python or C implementation does not count as self-hosting.

## Current status — Stage 0, partial Stage 1, and initial compiler-core slices

`selfhost/lexer.rpr` is the first executable frontend component implemented in Reaper itself. It performs scanning in Reaper functions and uses only the language's existing string indexing, lists, comparisons, loops, flow-independent control statements and standard collection operations. The Python interpreter is only the bootstrap host that executes this Reaper program.

The stage-0 lexer currently covers ASCII identifiers and digits, keywords, decimal/integer literals, strings and escapes, comments, newlines, punctuation, operators and source positions. It returns a structured error token for an invalid character or malformed string. The Python lexer accepts Unicode identifiers; that compatibility gap is deliberate and must be closed before the self-hosted lexer can replace the reference lexer.

### Stage 1: Pratt expression parser (partial)

`selfhost/parser.rpr` implements a Pratt expression parser in Reaper source. It consumes the same token-array shape emitted by the bootstrap lexer and builds compact array-form expression nodes. Implemented forms are literals, names, unary expressions, grouping, list literals, function calls, indexing and infix operators. The precedence table matches the reference parser, including the actual `::` flow operator and right-associative `**`.

The bootstrap assertions cover arithmetic precedence, exponentiation associativity, source-located unary nodes, flow composition, nested call/list/index expressions, missing delimiters and trailing-token errors. Declarations, function definitions, control-flow statements, block grammar and full canonical-AST parity remain incomplete. The Python parser is still the compatibility oracle.

### Compiler-core slices written in Reaper

`selfhost/compiler_core.rpr` adds an executable scalar-expression pipeline over the stage-local AST: symbol lookup, conservative type checks, source-positioned diagnostics, constant folding, stack-bytecode emission, stack-depth verification, and a versioned `REAPER-IR` envelope. The current lowering supports scalar literals, resolved names, unary operations, arithmetic, concatenation, comparisons and boolean operators. It deliberately rejects unsupported calls, collections and flow lowering instead of pretending they are native.

This is an initial compiler-core slice, not a complete semantic analyzer, optimizer, bytecode VM or native backend. The emitted instructions are verified structural IR; the file does not yet execute those instructions or generate a host object file.

### Reaper-native framework suite

`selfhost/frameworks.rpr` contains executable, bounded implementations and positive/negative assertions for eight framework families:

- **GalHero:** deterministic dependency ordering, unknown-edge validation, cycle rejection and dependency closure.
- **Call-and-Back:** ordered callback execution, bounded chains, result propagation and execution traces.
- **Stacked Options:** validated option layers, first-layer-wins resolution and deterministic merged output.
- **PerenosiMOST:** versioned schema envelopes and bounded adapter-based migrations.
- **MOST:** named unary operator contracts and ordered transformation traces.
- **Blau:** component/token blueprint validation, unique identifiers and parent/token references.
- **Shashio:** deterministic integer-key sharding and ordered shard merging.
- **Showel Fleppery CODE:** dependency-validated fragment graphs, deterministic source assembly and bounded text replacement.

These are real Reaper functions, not generated line-count padding. They are useful initial framework cores with explicit contracts and limits; broader production APIs, integration points and target-runtime evidence remain future work.

The existing Python test harness only launches these `.rpr` programs through the bootstrap interpreter and checks their single success marker. It does not reimplement framework or compiler behavior in Python.

## Bootstrap stages

| Stage | Reaper-written component | Current evidence / acceptance gate |
|---|---|---|
| 0 | Lexer | ASCII scanning and source positions execute in Reaper; Unicode and complete token-by-token parity remain open |
| 1 | Pratt expression parser | Expression grammar is implemented in Reaper; statement grammar and canonical AST parity remain open |
| 2 | Semantic analysis | Scalar expression type checks and symbol resolution exist; whole-program scopes, effects, regions and full differential parity remain open |
| 3 | Canonical IR and verifier | Versioned scalar expression IR and stack verification exist; canonical whole-program IR, verifier coverage and runtime execution remain open |
| 4 | Optimizer | Bounded scalar constant folding exists; fixed-point passes, equivalence checks and reproducible optimization remain open |
| 5 | Native code-generation frontend | Not complete; generated target output must build and pass the conformance suite |
| 6 | Bootstrap closure | Not complete; clean-room stage builds must rebuild themselves reproducibly |

## Non-negotiable rules

1. Reaper implementation logic belongs in `.rpr` sources; host code is limited to bootstrap, platform primitives and test orchestration.
2. Keep the Python implementation as a compatibility oracle until full differential parity is demonstrated.
3. Keep the C17 runtime/compiler track as the native execution substrate during bootstrap; do not claim it is a complete runtime until the full suite passes.
4. Every stage has positive, negative, regression, resource-limit and source-location tests.
5. A stage is not complete because its source file exists. It must pass the stated acceptance gate on a clean checkout.
6. Bootstrap builds must be deterministic and record source hashes, compiler version, target and build inputs.
7. No stage may silently add filesystem, network, process, shell or hardware authority to ordinary Reaper programs.

## Immediate next work

- Close Unicode identifier parity and complete keyword/operator token conformance in the Reaper-written lexer.
- Extend the Reaper-written parser with declarations, function definitions, blocks, conditionals, iteration and loop statements.
- Define the full canonical AST and compare Reaper parser output with the reference parser over a shared golden corpus.
- Add scoped symbol tables, mutability/effect checks and structured result propagation to the semantic layer.
- Extend the IR with typed values, basic blocks, source maps, call conventions, ownership and verifier rules.
- Add property and differential tests for optimizer semantics, bytecode execution and deterministic rebuilds.
- Implement an actual Reaper-written VM/native backend, then use it to rebuild the Reaper compiler in a clean bootstrap cycle.
