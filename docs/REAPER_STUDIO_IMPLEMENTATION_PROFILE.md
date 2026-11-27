# Reaper Studio — IDE implementation contract

**Status:** implementation baseline, not a claim of full IDE parity  
**Product:** Reaper Studio  
**Runtime:** existing Reaper interpreter and debugger APIs  
**Desktop UI:** Python standard-library Tkinter  
**Rulebook:** complete engineering requirement set, normalized into seven non-overlapping domains

## 1. Canonical numbering

The source rulebook contains a numbering collision: its editor/tooling ranges overlap the preceding and following domains. This implementation assigns stable, disjoint ranges while preserving the original order of the seven domains.

| Canonical IDs | Domain | Main implementation surface |
|---:|---|---|
| 001–096 | Performance and architecture | UI thread discipline, bounded work, incremental services, lifecycle |
| 097–192 | Editor and navigation | source editor, files, project tree, line/column navigation, search |
| 193–288 | Completion, analysis and refactoring | lexer/parser integration, diagnostics, symbol model, semantic services |
| 289–384 | Debugging, tests and execution | check/run, debugger, breakpoints, runtime traces, test runner |
| 385–480 | Git and collaboration | repository status, diffs, patches, review and safe integration |
| 481–576 | Extensions, automation and AI | extension contracts, task automation, assistant proposals and validation |
| 577–666 | Accessibility, security, localization and engineering culture | keyboard access, themes, localization, trust boundaries, documentation |

The ranges contain 96, 96, 96, 96, 96, 96 and 90 IDs respectively: 666 unique IDs, with no overlap or gaps. A requirement's ID is permanent. Splitting or merging requirements creates successor IDs and keeps the original ID as a deprecated alias; IDs are never reused.

## 2. Status vocabulary

| Status | Meaning | Evidence required |
|---|---|---|
| proposed | Candidate capability | owner and rationale |
| specified | Behavior and boundary are documented | contract and acceptance criteria |
| implemented | Executable code exists | implementation path and tests |
| verified | The implementation passed its gates | CI run or reproducible local evidence |
| deferred | Intentionally postponed | dependency and reason |
| deprecated | Superseded or removed | migration path and compatibility note |

A visual control, placeholder, roadmap item or reserved language token is not an implementation. No capability may be marked verified without a passing test or reproducible evidence. No performance claim may be marked verified without a benchmark and stated hardware/runtime conditions.

## 3. Current implementation baseline

The branch adds or strengthens the following usable foundations:

| Capability | State | Evidence / boundary |
|---|---|---|
| CODEX-66 capability browser | implemented | `reaper/codex66.py`, `reaper/codex66_ui.py`; 66 searchable items, explicit maturity states, JSON export and native editor command links |
| Native desktop entry point | implemented | reaper.desktop:main, already exposed as reaper-studio |
| Open, save, save as, new file | implemented | UTF-8 source files; unsaved-change confirmation |
| Project explorer | implemented | bounded depth and entry count; hidden/build folders excluded; symlinks not followed |
| Syntax coloring | implemented | deterministic lexical spans for comments, strings, numbers and canonical keywords |
| Line numbers and cursor position | implemented | editor canvas and status bar |
| Find and go to line | implemented | keyboard-accessible menu commands |
| Parse/check action | implemented | existing parser; no separate editor grammar |
| Run action | implemented | worker thread and UI-safe message queue |
| Runtime debugger | implemented | existing breakpoints, step, continue, variables and call stack |
| Embedded C workflows | implemented | existing project init, inspect and build actions retained |
| Light/dark/system theme | implemented | existing Reaper theme services retained |
| Language server (LSP) | implemented | versioned UTF-16 JSON-RPC, parser/structure diagnostics, background per-document symbol index |
| Structured local diagnostics | implemented | `reaper/ide_support.py`, `tests/test_ide_support.py`; source file, one-based start/end position, severity and stable diagnostic code; UI jumps to exact line/column |
| Completion, hover, rename, references | partial | keyword/symbol completion and lexical navigation/refactoring; no cross-file type resolution |
| AST/IR visual explorer | deferred | requires stable public AST/IR inspection API |
| Test explorer and coverage | deferred | requires test discovery and machine-readable test events |
| Integrated Git workflow | deferred | must use existing safe patch pipeline and explicit review |
| Plugin SDK and AI actions | deferred | requires permission model, sandbox and auditable proposals |
| DAP interoperability | implemented baseline | RuntimeDebugger bridge: launch, line breakpoints, statement stepping, stack and locals; no eval/step-out |

CODEX-66 is a metadata catalogue with implemented, partial, planned and unsupported states; it does not turn roadmap entries into features. The editor now exposes local LanguageService completion, current-document definition lookup, lexical references and current-document rename. It does not provide cross-file type inference, AST-safe refactoring or cloud AI.

The existing editor is a single-document workbench. Multi-tab sessions, cross-file semantic intelligence, integrated Git review and plugin execution are not claimed as complete.

## 4. Architecture boundaries

1. **The editor owns presentation, not language semantics.** Syntax highlighting consumes pure lexical spans. Parsing and diagnostics come from the canonical Reaper frontend.
2. **The runtime remains authoritative.** The IDE must not duplicate evaluation, type rules, or effect policy.
3. **The UI thread never runs user programs or builds.** Work is delegated to a worker; results return through a queue and the Tk event loop.
4. **Debugging is cooperative.** The IDE uses the runtime's debugger hook. The DAP adapter wraps that contract rather than inventing a second debugger; stepping is statement-boundary only.
5. **Project browsing is bounded.** The explorer limits depth and entries, skips hidden/generated folders, and never follows symlinks.
6. **No hidden authority.** Opening a project does not execute code. AI/plugin proposals do not run automatically. Build and patch application remain explicit user actions.
7. **No false sandbox claim.** Interpreter quotas are resource controls, not host-process isolation.
8. **Accessibility is functional.** Keyboard shortcuts mirror menu actions; status is textual; themes do not change program behavior.
9. **Compatibility is preserved.** Existing embedded C and debugger actions remain available while editor services are added.
10. **A capability is not complete until tested.** UI appearance alone does not satisfy acceptance.

## 5. Acceptance gates

### Editor and navigation
- Open and save UTF-8 .rpr and .most files without lossy conversion.
- Warn before discarding unsaved changes.
- Find and go-to-line work from both menu and keyboard.
- Project enumeration is deterministic, bounded, and does not follow symlinks.
- Highlight spans are non-overlapping offsets into the unchanged source text.

### Responsiveness and execution
- Long-running source does not block the Tk event loop.
- Worker threads never mutate Tk widgets directly.
- Output is delivered in order through the UI queue.
- Runtime failures are surfaced in the output panel; the UI remains usable.
- The UI does not claim that Stop cancels execution until interpreter cancellation is implemented.

### Debugger
- Existing breakpoints, step, continue, variables and call stack remain functional.
- A stopped debug session returns control to the editor.
- Source locations remain compiler/runtime-owned; the IDE does not infer semantic locations from colorization.

### Security and trust
- Opening a folder does not run its contents.
- Project browsing does not traverse symlinks or generated dependency trees.
- Extension and AI proposals require explicit review and a constrained execution boundary before they can become actions.
- Secrets and environment variables are not exposed in diagnostics or logs by default.

### CI
- Python unit tests pass, including editor-service tests.
- The package compiles on supported Python versions.
- Native C and interpreter test suites remain green.
- Windows desktop packaging is built and smoke-tested before release claims are made.

## 6. Next implementation sequence

1. **Stabilize editor core:** add UI-level smoke tests, scroll-synchronized line numbers, robust error-to-source navigation and multi-tab document state.
2. **Diagnostics service:** implemented for local type-check diagnostics; parser/LSP diagnostics retain their compiler-owned source spans. Extend the normalized contract to semantic cross-file diagnostics after the compiler-owned typed-IR API is stable.
3. **Semantic protocol:** extend the implemented versioned JSON-RPC/LSP service with compiler-owned AST and typed-IR data.
4. **Completion and navigation:** replace lexical-only resolution with scope-aware symbols, type-aware completion, semantic tokens and AST-safe refactoring.
5. **Test and build panels:** machine-readable task events, cancellable subprocesses, progress, logs and artifact links.
6. **Git panel:** status/diff/branch views using the repository's verified patch proposal/apply/rollback workflow; no implicit commits or merges.
7. **Plugin and AI layer:** signed/declared capabilities, explicit permissions, proposal-first edits, audit trail and sandboxed execution.
8. **Release readiness:** accessibility checks, localization, Windows/macOS/Linux packaging, crash recovery and reproducible release artifacts.

## 7. Definition of done

Reaper Studio is a complete IDE only when the core editor, semantic language services, execution/debugging, test/build workflow, safe Git collaboration, extension model, accessibility and security gates are all implemented and verified. Until then, each capability must be reported with its actual status and evidence.
