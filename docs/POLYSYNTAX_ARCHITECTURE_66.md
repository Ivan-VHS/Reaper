# Reaper PolySyntax Architecture — 66 engineering rules

**Project:** Reaper  
**Maintainer:** Ivan-VHS  
**Status:** staged implementation; versioned profile registry and reference-front-end integration delivered in this branch  
**Scope:** simultaneous syntax profiles, mixed-syntax modules, frontend tooling, canonical compiler IR, execution backends, and future grammar adapters

## 1. Non-negotiable architecture

Reaper supports multiple surface syntaxes as views of one language. A profile may change exact keyword spellings, operators or grammar only through an explicit adapter, but it must not create a separate runtime or semantic universe.

`source → selected profile → tokens → surface AST → canonical AST → type/semantic checks → canonical IR → verified backend`

The stable built-in profiles in this increment are:

| Profile | Selection | Surface form | Maturity |
|---|---|---|---|
| `reaper` | `.rpr` or default | Canonical Reaper syntax; existing Russian aliases remain compatible | Stable core |
| `reaper-flow` | `.rflow` | Flow-first Reaper expressions and pipelines | Core grammar |
| `most-ru` | `.most` | Exact Russian MOST aliases | Core aliases |
| `most-uk` | `.most-uk` | Exact Ukrainian MOST aliases | Core aliases |
| `classic` | `.rclass` | `let/var/set/fn/return/print/if/else/for` aliases | Core aliases |

A profile is selected by an explicit API/CLI option or by a registered file extension. The compiler never tries to infer a grammar from arbitrary source text. For backward compatibility, in-memory sources and unknown extensions retain the historical Reaper profile unless the caller supplies one explicitly.

All built-in profiles use the existing Reaper core grammar. Alias spellings are converted into canonical token kinds before parsing. Source token text and line/column coordinates remain available for diagnostics. AST node kinds, type checking, IR operations and runtime behavior are profile-independent.

## 2. Frontend and module behavior

- `reaper.syntax_profiles` owns profile descriptors, versions, exact aliases, extension ownership and the registration API.
- `Lexer` resolves a profile once per source and maps aliases to canonical token kinds.
- `parse(source, filename, syntax=None)` exposes explicit selection while preserving the old call signature.
- `reaper --syntax PROFILE` overrides extension selection for checks and execution; otherwise the extension selects the mode.
- `LanguageService` uses the file profile for parsing, declaration indexing, keyword completion and keyword-safe renames.
- Studio highlighting accepts a filename or explicit profile; project discovery recognizes all built-in Reaper source extensions.
- Module imports may target any registered Reaper source extension. A module is parsed using its own extension/profile and linked into the shared module environment. Import caching, cycle detection, path resolution and export isolation remain common.
- Cross-profile imports do not imply permission escalation, implicit conversions, or separate global namespaces.

The registry accepts additional exact-alias profiles. A new grammar or embedded DSL is not enabled merely by registering aliases: its parser adapter must produce valid canonical Reaper AST nodes and pass the same verification and conformance suites.

## 3. Sixty-six rules

### A. Core, AST and compiler pipeline (1–12)

1. Maintain one canonical AST/IR contract shared by every profile.
2. Keep surface spelling separate from node semantics.
3. Separate lexing, parsing, lowering, validation and execution into explicit stages.
4. Desugar surface-only constructs before type checking and optimization.
5. Preserve the source profile and source coordinates in diagnostics.
6. Retain source spans/provenance for nodes created during lowering.
7. Make profile lowering deterministic and reproducible.
8. Register profiles declaratively; do not scatter dialect checks through parser code.
9. Keep the executable core smaller than its surface-language catalogue.
10. Keep the runtime unaware of source syntax and operate on canonical IR/runtime values.
11. Isolate recoverable errors in embedded or imported language blocks.
12. Resolve names, modules, imports and exports in one shared symbol model.

### B. Selection and coexistence (13–24)

13. Select syntax explicitly through extension, CLI/API option, project setting or a future block header.
14. Do not use content guessing to choose a compiler grammar.
15. Permit mixed-profile projects and modules through the canonical interface.
16. Require explicit delimiters and adapters for embedded DSL blocks.
17. Reject unmarked mixing of incompatible grammars in one expression.
18. Define string, escape, comment and delimiter behavior per profile without leaking state.
19. Make import/export contracts identical across profiles.
20. Use one module graph, canonical path model and namespace policy.
21. Version profiles independently from the runtime and compiler.
22. Specify keyword/identifier precedence and collision behavior.
23. Keep localized layers as exact aliases over canonical operations; do not guess morphology or synonyms.
24. Make profile changes incapable of altering capabilities, permissions or hidden effects.

### C. Lexer, parser and performance (25–36)

25. Select parser strategy per grammar adapter while preserving the canonical AST boundary.
26. Resolve grammar ambiguity by explicit grammar rules, not accidental parser order.
27. Publish operator precedence and associativity for each grammar adapter.
28. Keep keyword tables scoped to the selected profile.
29. Cache profile resolution and make document parsing incremental.
30. Recover at declared synchronization points and report multiple independent errors where possible.
31. Bound nesting, recursion, token count and source size.
32. Keep parse complexity predictable under adversarial input.
33. Normalize source encoding and line endings while retaining correct source offsets.
34. Keep indentation-sensitive and delimiter-sensitive grammars isolated.
35. Avoid expensive per-file reflection, regex compilation and needless allocation.
36. Maintain per-profile parse benchmarks for latency, memory and recovery behavior.

### D. Types, runtime and code generation (37–48)

37. Apply one type system and one contract model to every profile.
38. Report source-level concepts and types, not internal lowering details.
39. Use a common error/result/exception contract across modules and backends.
40. Preserve one memory ownership, resource lifetime and cleanup model.
41. Generate deterministic, readable code for supported native targets.
42. Preserve source maps for diagnostics, debugging, profiling and stack traces.
43. Prohibit silent coercion merely because a value came from another profile.
44. Use one async, task, event and cancellation model when those features are implemented.
45. Define one ABI and calling convention at cross-module and foreign-function boundaries.
46. Verify canonical IR invariants immediately after lowering.
47. Add syntax sugar only when it improves clarity without multiplying equivalent forms.
48. Provide one deterministic AST/IR serialization format with source provenance.

### E. IDE, quality and evolution (49–66)

49. Provide profile-aware formatting without rewriting embedded foreign blocks.
50. Run common lint and static-analysis rules on canonical semantics.
51. Expose profile-aware highlighting, completion, navigation, rename and diagnostics through IDE/LSP.
52. Run tests through one runner regardless of source profile.
53. Keep golden fixtures for tokens, AST, IR, output and diagnostics.
54. Fuzz empty, malformed, deeply nested, mixed-encoding and Unicode input.
55. Test calls, imports, exports and error propagation between every supported profile pair.
56. Maintain one specification with profile-specific syntax tables and examples.
57. Remove or quarantine syntax branches that are not tested and tool-supported.
58. Review the ongoing parser, editor, documentation and test cost before adding a profile.
59. Supply deterministic migrations for profile-version changes.
60. Gate experimental grammar adapters behind explicit opt-in and version pins.
61. Diagnose overlapping aliases, operators and grammar conflicts at registration or compile time.
62. Keep runtime data, string contents and templates separate from syntax markers.
63. Use one vocabulary for AST nodes, types, diagnostics and profile identifiers.
64. Review readability and learnability for every surface syntax.
65. Measure profile usage, parse failures, diagnostics and compilation latency without collecting source text by default.
66. Preserve one meaning across many forms: diversity of syntax, unity of semantics, safety and execution.

## 4. Frontend/backend ownership

| Layer | Responsibilities | Required invariant |
|---|---|---|
| Profile registry | IDs, versions, extensions, keyword aliases, maturity | Unambiguous, immutable profile snapshots |
| Lexer | Exact alias mapping, token positions, lexical limits | Same canonical token kinds for equivalent constructs |
| Parser/adapter | Profile grammar and error recovery | Emits canonical Reaper AST |
| Semantic frontend | Symbols, scope, types, effects and contracts | No semantic branch based only on profile ID |
| Lowering | Desugaring, source provenance and deterministic IR | Equivalent constructs produce equivalent IR operations |
| IR verifier | Operand, type, control-flow and resource invariants | Reject malformed IR before execution |
| Reference runtime/VM | Values, calls, modules, errors, memory and effects | Identical observable behavior across profiles |
| Native backend | Lower supported canonical constructs to C17 | Feature-by-feature differential conformance |
| IDE/LSP | Contextual highlight, completion, navigation and diagnostics | Uses the same profile resolver and parser contracts |
| CI/tooling | Golden tests, fuzzing, benchmarks and compatibility matrix | No profile is stable without end-to-end evidence |

## 5. Implemented now vs. explicit gaps

**Implemented in this branch:** versioned built-in profile registry; extension and explicit API/CLI selection; canonical keyword-kind mapping; classic imperative aliases; Russian and Ukrainian MOST aliases; flow-first profile identification; mixed-profile module imports; profile-aware IDE indexing, completion, rename validation and highlighting; shared parser, AST, type checker, IR and runtime path; native AOT entry points accept the selected profile.

**Not claimed as complete:** arbitrary grammar replacement; embedded DSL block parsing; multiple independent operator grammars; full incremental AST reuse; full source-span tracking on every generated node; exhaustive syntax error recovery; complete C17 parser/IR parity; language-level async/ownership constructs that remain unimplemented in the core.

The current low-level C17 lexer/parser track is still a narrower native frontend (the C parser handles expression ASTs). The reference Python frontend and AOT compiler share the selected profile and canonical Reaper AST for the currently supported native subset. The C17 native parser must adopt the same profile table and pass differential fixtures before it is described as profile-parity complete.

## 6. Acceptance gates

A profile can be marked **stable** only after: profile registry validation; parser and source-location fixtures; canonical AST/IR golden tests; type and runtime parity tests; mixed-profile module tests; formatter/linter/LSP support; malformed-input fuzzing; source-map verification; documented migration policy; and measured parse performance. Alias-only profiles may reuse the core grammar suite, but each alias must still have collision, Unicode and end-to-end tests.

No profile may redefine authority, filesystem access, FFI permission, resource limits, memory policy or runtime semantics.
