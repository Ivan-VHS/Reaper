# Reaper Polyglot Code

## Purpose and boundary

Polyglot Code is Reaper's local-first system for absorbing programming languages as engineering environments rather than memorising syntax. It is intentionally separate from `reaper polyglot`, which handles natural-language immersion and phrase review.

The system turns the learning loop into persistent engineering evidence:

- one profile per target programming language, with known languages, current fluency level, language family, goal and daily time budget;
- a six-stage roadmap from toolchain setup through production architecture;
- a concept map covering types, execution, memory, errors, concurrency, modules, standard library, testing, idioms, ecosystem and interoperability;
- explicit cross-language comparisons that record the problem, the model in a known language, the model in the target language and the trade-off;
- language-neutral katas with acceptance checks and manually recorded completion;
- an idiom notebook that captures native patterns and the anti-pattern they replace;
- an error journal that preserves symptom, root cause, fix and reusable lesson;
- adaptive daily plans, practice sessions, progress diagnostics and portable JSON export.

This is a tracking and practice engine. It does not claim to automatically measure programming fluency or judge submitted code.

## Storage, privacy and safety

The default database is:

- Windows: `%USERPROFILE%\\.reaper\\polyglot-code.sqlite3`
- Linux/macOS: `~/.reaper/polyglot-code.sqlite3`

Set `REAPER_POLYGLOT_CODE_HOME` to choose another directory, or pass `--db PATH` immediately after `polyglot-code`.

All learner data stays in a local SQLite database. The subsystem performs no network requests, telemetry, automatic downloads or uploads. It never installs or runs compilers, package managers, source files or learner programs. The `toolchain` command only checks whether known executable names are present on `PATH`.

The kata completion state and self-assessment score are learner-entered records. Reaper does not execute the solution, inspect arbitrary project folders or certify correctness. Use a language's official compiler, formatter, linter, tests and debugger for actual verification.

## Quick start

~~~sh
# Build a Rust profile using C/C++ experience as the comparison baseline
reaper polyglot-code init Rust --known C,C++ --level working \
  --goal "Understand ownership and idiomatic systems code" --minutes 60

# Inspect the toolchain and staged learning route
reaper polyglot-code toolchain
reaper polyglot-code roadmap
reaper polyglot-code concept list

# Compare one mental model across languages
reaper polyglot-code compare memory --known-language C++ \
  --known-model "References, RAII and explicit ownership conventions" \
  --target-model "Ownership and borrowing checked by the compiler" \
  --tradeoff "More explicit constraints in exchange for stronger guarantees"

# Track mastery only when you have evidence
reaper polyglot-code concept update memory --status understood \
  --notes "Borrowing rules are clear" \
  --evidence "Implemented a slice API and explained its lifetime"

# Practise, then preserve the result
reaper polyglot-code kata list --stage 2
reaper polyglot-code kata complete sem-01 --score 5 \
  --solution experiments/value-semantics.rs \
  --notes "Observed moves and borrowed references"
reaper polyglot-code idiom add "Result propagation" --pattern "? operator" \
  --anti-pattern "Nested match ladders that discard error context" \
  --notes "Propagate expected failures; add context at abstraction boundaries"

# Capture the debugging lesson and the practice session
reaper polyglot-code error add "Borrow after move" \
  --symptom "value used after it was moved" \
  --cause "Ownership transferred into a consuming function" \
  --fix "Borrow the value or clone only where ownership requires it" \
  --lesson "Check parameter ownership before choosing a call signature"
reaper polyglot-code session --minutes 45 --mode coding \
  --notes "Implemented parser exercise and boundary tests" --score 4

# Review progress and create a portable backup
reaper polyglot-code plan
reaper polyglot-code diagnose
reaper polyglot-code report
reaper polyglot-code export --output rust-learning.json
~~~

When more than one target profile exists, pass `--target LANGUAGE` immediately after `polyglot-code`, for example:

~~~sh
reaper polyglot-code --target Rust report
reaper polyglot-code --target Python plan --minutes 30
~~~

## The six-stage roadmap

| Stage | Focus | Exit evidence |
|---:|---|---|
| 0 | Environment and toolchain | Reproducible build, format, lint, test and debug commands |
| 1 | Syntax, functions, collections and modules | Small programs written without syntax-by-memory friction |
| 2 | Types, runtime, memory, errors and concurrency | A written execution model plus experiments for edge cases |
| 3 | Standard library and mini-projects | CLI utility, data transformer and a stream/network exercise |
| 4 | Idioms, tests, code reading and diagnostics | Refactored exercises, regression tests and a useful error journal |
| 5 | Architecture, profiling and production fluency | Measured performance decisions and a maintained project |

The stage durations are orientation ranges, not deadlines or automatic advancement rules.

## Concept model

Each concept has one of four states:

- `unseen`: not yet investigated;
- `in_progress`: currently being studied or tested;
- `understood`: the learner can explain the mechanism and demonstrate it;
- `idiomatic`: the learner can apply it naturally and recognise the native conventions.

Concept keys are stable CLI identifiers:

| Key | Area |
|---|---|
| `toolchain` | compiler/runtime, package manager and feedback loop |
| `syntax` | bindings, values, control flow and core expressions |
| `functions-scope` | functions, captures, scope and closures |
| `types` | static/dynamic typing, inference, generics, interfaces and sum types |
| `execution` | evaluation, runtime services and execution behaviour |
| `memory` | stack/heap, ownership, references, lifetimes, copying and GC |
| `errors` | exceptions, result types, error codes, panic and recovery boundaries |
| `concurrency` | threads, tasks, async, channels, cancellation and shared state |
| `modules` | imports, packages, visibility and dependency boundaries |
| `stdlib` | collections, strings, I/O, time and core library APIs |
| `io-data` | files, streams, encodings and structured data validation |
| `testing-debugging` | tests, diagnostics, debugger and regression workflow |
| `idioms` | native patterns, naming, decomposition and live-code reading |
| `ecosystem` | package health, build, release and dependency discipline |
| `architecture` | architecture, profiling, allocation and abstraction costs |
| `interop` | ABI, FFI, layout and ownership across language boundaries |

An item should move to `understood` or `idiomatic` only when the notes/evidence field records a concrete demonstration, not merely after reading a page.

## Mental-model transfer

For every important concept, record the same three questions:

1. What problem does this mechanism solve?
2. How is the same problem handled in a language already known?
3. What trade-off changes in safety, performance, readability, complexity or runtime cost?

The `compare` command stores one comparison per target concept and known language. It is deliberately explicit: Reaper does not invent equivalence between language features or imply that two mechanisms have identical semantics.

## Language-family focus

When `--family auto` is used, Reaper assigns a broad heuristic based on the language name:

- `manual-memory`: C, C++, Zig and assembly — prioritise allocation, layout, pointer safety and lifetime discipline;
- `ownership`: Rust — prioritise move, borrow, aliasing and lifetime rules;
- `garbage-collected`: Go — include allocation profiles and GC behaviour;
- `managed-runtime`: Java, C#, Kotlin, Swift, Dart and Scala — examine runtime, value/reference semantics and concurrency model;
- `dynamic`: Python, JavaScript/TypeScript, Ruby, PHP, Lua and Perl — make contracts, validation and tests explicit;
- `functional`: Haskell, OCaml, F#, Elm, Clojure, Erlang and Elixir — focus on immutability, composition and pattern matching;
- `multi-paradigm`: languages not covered by the simple name map.

This is a planning hint, not a full taxonomy or a compiler capability claim. Override it with `--family` when a language has a different runtime or programming model.

## Practical workflow

1. Start with one target profile and list the languages already known.
2. Set up the real toolchain. Use `toolchain` for a read-only PATH inventory, then verify versions and commands using the official tools yourself.
3. Read one focused reference section and one example from a maintained codebase.
4. Implement a small task and write tests for boundaries and failure paths.
5. Record the mental-model comparison and any surprising compiler/runtime diagnostic.
6. Refactor the solution into the language's idioms; add an idiom note only when you have a concrete pattern and source.
7. Finish the session with a short note naming the next experiment.

The adaptive plan allocates the configured time budget to conceptual modelling, coding, testing, reading, refactoring and review. It tilts early profiles toward the foundation and experienced profiles toward live code and project work. Ownership/manual-memory profiles receive an extra memory-model emphasis; dynamic and managed profiles receive additional attention to contracts and allocation behaviour. The plan is a suggestion, not a timer or an enforced schedule.

## Command reference

| Command | Purpose |
|---|---|
| `init LANGUAGE --known A,B` | Create or update a target profile |
| `profile` | List profiles |
| `toolchain` | Check known tool names on PATH, without executing them |
| `roadmap [--stage N]` | Show the six learning stages |
| `concept list [--status STATE]` | Inspect the concept map |
| `concept update KEY --status STATE` | Store mastery, notes and evidence |
| `compare KEY --known-language NAME ...` | Record a cross-language model and trade-off |
| `kata list [--stage N]` | Browse practical exercises |
| `kata complete ID` | Record a completed exercise and optional score/evidence |
| `idiom add NAME --pattern TEXT` | Store an idiom and the anti-pattern it replaces |
| `idiom list` | Review the idiom notebook |
| `error add TITLE --symptom ... --cause ... --fix ... --lesson ...` | Record a debugging lesson |
| `error list` | Review recent error patterns |
| `plan [--minutes N]` | Create the adaptive daily plan |
| `session --minutes N --mode MODE` | Log a completed practice session |
| `diagnose` | Show outstanding concepts |
| `report` | Summarise mastery, katas and practice |
| `export [--output FILE]` | Export the profile and its learning records as JSON |

Run `reaper polyglot-code COMMAND --help` for exact options. The database and target selectors go before the subcommand.

## Current implementation boundaries

The Python reference implementation provides persistent profiles and learning records, a roadmap, concept diagnostics, comparison notes, kata tracking, idiom/error journals, PATH-only toolchain discovery, adaptive planning, reporting and JSON export.

The following are not implemented and are not simulated:

- automated code grading, static analysis or semantic equivalence checking;
- compiler/runtime installation or execution of learner programs;
- automatic retrieval of documentation, source code or examples from the network;
- LSP/editor integration, debugger orchestration or automatic test-runner adapters;
- AI code review, generated explanations or automatic proficiency certification;
- a native C17 learning engine or a dedicated Reaper Studio learning panel.

The system is useful as a local engineering learning notebook and workflow engine today. Execution, diagnostics and code-quality checks remain the responsibility of each target language's official toolchain.
