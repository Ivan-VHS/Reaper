# OmniCore Language Evolution Engine — M1

**Status:** implemented Python reference-package ingestion milestone; native C17 integration is a later acceptance-gated phase.

OmniCore is the external-language observation and evolution-proposal subsystem of Reaper. It does not create a second language or replace Reaper's syntax, parser, canonical IR or EV0 evidence gate. Reaper remains the target language. The first milestone establishes a bounded, reproducible pipeline from source repositories and compiler artifacts to a normalized structural representation, semantic evidence and reviewable extension proposals.

## 1. Implemented pipeline

\`\`\`text
Local source tree
  -> bounded artifact discovery
  -> language / grammar / build-manifest / test / trace classification
  -> Python AST | optional installed Tree-sitter grammar | structural fallback
  -> normalized UAST + source spans + OpaqueNode recovery
  -> static semantic feature evidence + imported runtime-trace observations
  -> expressiveness-gap classification
  -> utility / complexity gate
  -> deterministic lang-evo-* proposal + provenance graph + JSON memory
\`\`\`

### Ingestion and artifact discovery

- Recognizes source extensions for Python, C/C++, Rust, Go, Java, JavaScript/TypeScript, C#, Kotlin, Swift, Ruby, PHP, Scala, Lua, Julia, Zig, Nim, Haskell, OCaml, Elixir, Erlang, Dart, SQL, shell, WebAssembly text, Reaper and other listed families.
- Finds grammar artifacts such as ANTLR \`.g4\`, PEG, Pest, Lark, EBNF/BNF, Bison/Yacc and Lex files.
- Reads build manifests including \`pyproject.toml\`, \`package.json\`, \`Cargo.toml\`, \`go.mod\`, CMake, Make, Gradle, Maven, Composer, Swift Package and related descriptors without running their build tools.
- Identifies test/fixture paths and imports JSONL runtime trace records as observational evidence.
- Records SHA-256 fingerprints, file sizes, relative paths, parser identity and source locations.

### Parsing and UAST

- Python uses the standard-library \`ast\` module for a real syntax tree.
- If \`tree_sitter_language_pack\` or \`tree_sitter_languages\` is already installed and exposes a grammar for the source language, OmniCore uses that grammar. These packages are optional and are not runtime dependencies of Reaper.
- Without a compatible parser, other languages use a conservative lexical/structural adapter. It detects declarations, control flow, calls and balanced-delimiter failures but does **not** claim a complete grammar, typed AST or semantic equivalence.
- Malformed input is retained as \`OpaqueNode\` evidence with source lines instead of being silently guessed.
- The Python API exposes the UAST. CLI JSON includes it only when \`--include-uast\` is supplied, to keep ordinary reports compact.

### Semantic observation and synthesis

The current evidence extractor recognizes recurring signals for asynchronous execution, ownership/borrowing, algebraic types, error models, pipelines, resource scopes, I/O effects, memory management, metaprogramming and contracts. Imported traces add observed event and runtime type summaries. Each feature is marked as heuristic/static or trace-derived evidence; none is presented as proof of a language's complete semantics.

Proposals are classified as direct/compositional/semantic gaps and assigned a deterministic ID, profile, utility score, complexity cost, evidence count, source provenance and explicit guardrails. Pipeline composition is compared against Reaper's existing \`::\` operator rather than creating a duplicate primitive. Proposals below the utility/complexity threshold remain visible but are not marked ready for review.

## 2. Safety, determinism and control

Default budgets:

| Limit | Default |
|---|---:|
| Candidate files | 2,000 |
| Single file size | 2,000,000 bytes |
| Total bytes read | 50,000,000 bytes |
| UAST nodes per file | 2,500 |
| Proposal evidence | 2 occurrences |

The scanner prunes common generated/dependency directories, avoids symlinks, skips binary and non-UTF-8 files, and never invokes compilers, shells, tests, programs, package managers or external services. It makes no network requests and does not modify scanned source or the Reaper language core.

\`read-only\`, \`co-design\`, \`autonomous\` and \`revision\` are workflow labels. In M1, all are non-executing and proposal-only: \`autonomous\` means automatic discovery and proposal generation, not automatic code mutation or publication. A user may explicitly request atomic report/proposal/memory output paths. The memory journal is a local JSON file containing source fingerprints, feature sightings, proposal decisions and a lightweight concept graph.

The tool's own report must not be treated as a security sandbox. It analyzes text; it does not execute untrusted programs. Runtime traces are accepted as untrusted observational input and require provenance review.

## 3. CLI

\`\`\`sh
# Analyze one source file or an entire local repository
reaper absorb ./external-project
reaper absorb ./external-project --mode co-design

# Stable machine-readable report, with optional full UAST
reaper absorb ./external-project --json --include-uast --output ./omnicore-report.json

# Persist deterministic proposal files and cross-run observation memory
reaper absorb ./external-project \\
  --proposal-dir ./.reaper/evolution/proposals \\
  --memory ./.reaper/evolution/memory.json

# Bound the analysis explicitly
reaper absorb ./external-project --max-files 500 --max-file-bytes 1000000 --max-total-bytes 10000000
\`\`\`

The Python API is \`OmniCoreEngine(path, ...).run()\`. The result includes per-file analyses, UAST, normalized evidence, proposals, artifacts, a lightweight knowledge graph and an explicit execution policy. \`AbsorptionReport.to_dict(include_uast=True)\` exports full UAST details.

## 4. Acceptance and limitations

M1 has unit coverage for multi-language ingestion, Python AST parsing, conservative Rust parsing, malformed-source recovery, grammar/manifest/trace artifacts, deterministic proposal IDs, bounded scanning, report output and non-modification guarantees.

Not yet implemented: full parsers for every language, ANTLR/PEG grammar compilation, semantic type inference across languages, CFG/call-graph construction, static ownership/effect checking, execution instrumentation, sandboxed runtime replay, differential equivalence, grammar/type-checker/IR code generation, round-trip translation and automatic publication. These are separate milestones and must not be described as shipped capabilities.

### Next milestones

- **M2 — parser adapters:** versioned adapter protocol, richer Tree-sitter/ANTLR/PEG grammar integration, CST preservation and incremental parsing.
- **M3 — semantic IR:** typed declarations, symbol/type relations, CFG/call graph, effects, error models and ownership facts.
- **M4 — runtime observer:** opt-in harness contracts, isolated execution provider, trace schema validation, quotas and provenance.
- **M5 — synthesis and verification:** typed extension specs, grammar/type rules, staged IR transforms, property/fuzz/differential tests and rollback snapshots.
- **M6 — code generation:** source maps, Reaper generation, foreign backend adapters and round-trip conformance.
- **M7 — native integration:** C17 ingestion/evidence contracts and convergence with Reaper's canonical IR and native EV0 gate.

No milestone may mark a feature implemented based on a document or proposal alone. A feature requires executable code, a public contract, positive/negative tests, CI evidence and an explicit compatibility decision.
