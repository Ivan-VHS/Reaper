# Reaper Studio UI/UX and Language-Environment Architecture

**Status:** target architecture layered over the Python reference runtime, developing native C17 track and Tkinter Studio. A requirement here is not an implemented language feature unless code and tests demonstrate it.

## 1. Product fit

Reaper is a flow-first programming language. Studio must make explicit data flow visible while keeping parsing, execution, diagnostics and audit inspectable. The current Studio provides a source editor, Open/Save/Check/Run/Debug, breakpoints, Output, Variables, Call Stack and a status line. Preserve this compact workflow while adding progressive disclosure.

The Python reference interpreter remains the compatibility authority until native parity is demonstrated. The native C17 lexer/parser/IR work must not be presented as a complete native interpreter.

## 2. Six Anatidae articles as UI invariants

| Article | Invariant | Reaper Studio application |
|---|---|---|
| I. Water-repellent plumage | Strict containment | Editor, diagnostics, variables, stack, modules, audit and settings have explicit ownership; overlays must not obscure source unexpectedly. |
| II. Calm surface, strong engine | Simple surface; inspectable internals | Check/Run/Debug remain one-step actions. AST, IR, types, effects, quotas, module graph and audit are optional inspectors. |
| III. Rudder and balance | Stable orientation | Active file, engine, line/column, run state and environment remain visible through panel changes. |
| IV. Webbed feet | Adaptive layout | Compact editor/output view; standard three-pane Studio; large-screen inspectors and MOST matrix. |
| V. Precise bill | Precise commands/diagnostics | Search, symbol lookup and errors jump to exact spans without discarding editor state. |
| VI. Flock and wake | Composable modules and mutual rights | Import/export, ABI, package metadata and license evidence are shown at module boundaries. |

## 3. Adaptive Studio layout

Use logical client width after OS DPI scaling; support 7680×4320 at 100–300% system scaling.

- **Compact (≤1280 logical px):** editor is primary; Open/Save/Check/Run/Debug remain visible; secondary actions move to overflow. Output, Variables and Call Stack remain tabs below. Diagnostics are concise and source-linked.
- **Standard (1281–2560):** project/symbol navigator, editor and runtime inspector. Inspector tabs: Output, Diagnostics, Variables, Call Stack, Audit. Status strip shows engine, file, execution state and cursor.
- **Wide / 4K (2561–3839):** add module/dependency graph and semantic inspector. MOST matrix opens beside editor with searchable `Ei ⊗ Ej` detail.
- **8K (≥3840 logical px):** full developer cockpit—navigation, editor, output/trace, AST/IR/type/effect inspectors, module graph and MOST matrix. Keep text measure around 68–96 characters; use independent panes, not one panoramic text block.

Physical resolution alone must not trigger 8K mode: an 8K panel at 200% scaling has a smaller logical work area and must receive a correspondingly compact layout.

## 4. Language environment and 20×20 matrix

The 20 concepts are a navigable semantic basis:

| Range | Responsibility |
|---|---|
| E1–E4 | Russian-language composition, adoption, code representation and algorithms |
| E5–E9 | machine instructions, formal constraints, tooling, computation and systems |
| E10–E13 | instruction catalogue, command language, syntax and semantics |
| E14–E16 | declarative, imperative and procedural execution models |
| E17–E19 | ownership, module author rights and third-party rights |
| E20 | live feedback and creative flow |

All 400 directed pairs `Ei ⊗ Ej` are addressable in the MOST navigator. A pair records a semantic relationship and possible implementation work; it does not automatically create a grammar production, builtin, compiler backend or executable capability.

Use [MOST 400 combinatorial matrix](MOST_400_COMBINATORIAL_MATRIX.md) and [MOST implementation status](MOST_IMPLEMENTATION_STATUS.md) as source of truth. Display statuses **implemented**, **specified**, **planned** and **not applicable**; implemented claims require code/test evidence.

### Staged language-ingestion pipeline

1. Register source language, version, license, attribution and scope.
2. Describe tokens, grammar, type/ownership model, effects and execution semantics.
3. Map supported constructs to Reaper syntax/AST/IR; report loss and incompatibilities explicitly.
4. Run parser, semantic, negative and differential conformance tests.
5. Enable only verified subsets; keep unsupported syntax as inspectable metadata.

Reaper syntax and standard library remain its own. Compatibility adapters do not imply ownership of third-party languages or permission to reuse copyrighted implementation code.

## 5. Tokenized color and density engine

Editor, tabs, trees, matrix, dialogs and diagnostics consume one semantic token map:

- `bg-pond`, `bg-surface`, `bg-elevated`: workspace, panes and overlays.
- `fg-primary`, `fg-secondary`, `fg-muted`: source, explanations and metadata.
- `accent-primary`, `accent-secondary`, `accent-warm`: action, semantic links and live execution.
- `status-ok`, `status-warn`, `status-danger`: valid, advisory and failed states.

Presets: **Morning Pond** (pearl/teal/amber), **Twilight Water** (slate/mint/coral), **Northern Ice 8K** (high contrast and strong focus), **Warm Vibe** (cream or chocolate/amber). Include normal, high and extra-high contrast. Syntax meaning must survive monochrome and must not rely on hue alone.

Theme settings include `uiScale` 80–250%, editor/catalogue font size, line height, border strength and Compact/Balanced/Spacious density. All panes update in one transaction. Persist preferences in a versioned user-settings file, never in source files.

## 6. Motion, search and precision

- Transitions 120–220 ms; honor operating-system reduced-motion settings.
- Focus outlines scale to about 1.5–3 physical pixels at 8K.
- Interactive targets at least 40 logical px high; 44 preferred.
- Search commands, files, tokens and matrix pairs; exact matches rank first.
- Opening AST/IR, changing theme or selecting a matrix cell must not overwrite source or move the caret unexpectedly.

## 7. Rights, localization and isolation

- Every imported language, syntax table, code sample, module and package carries provenance, version and license metadata.
- E17 tracks ownership; E18 protects module authors; E19 audits third-party license/attribution obligations.
- Distinguish unknown, incompatible and verified license states; a green marker is not a legal opinion.
- Target UI locales: English, Ukrainian, Russian and Simplified Chinese. UI labels localize independently of Reaper keywords, grammar, diagnostics IDs and serialized keys.
- Keep execution quotas, filesystem permissions, resource scopes and native FFI trust gates visible at relevant boundaries.

## 8. Implementation sequence and acceptance gates

1. Centralize ttk/editor palette, typography and the four presets.
2. Add DPI-aware pane composition and resize tests for compact, standard, 4K and 8K.
3. Add command palette and semantic navigator over the token catalogue and MOST matrix.
4. Add evidence-backed statuses for syntax, IR, runtime and language adapters.
5. Add locale resources, accessibility checks and UI smoke tests.

Acceptance: Check/Run/Debug behavior remains unchanged; no unsupported native capability is implied; tokens update consistently; editor text remains readable; matrix navigation preserves context; reduced motion/keyboard navigation work; parser/runtime tests and desktop CI pass.

## 9. Related architecture

- [Constitution of the Ducks](ANATIDAE_CONSTITUTION.md) · [MOST language specification](MOST_LANGUAGE_SPEC.md)
- [MOST 400 matrix](MOST_400_COMBINATORIAL_MATRIX.md) · [Runtime platform](RUNTIME_PLATFORM.md)
- [Project federation](PROJECT_FEDERATION_MATRIX.md)


## White-blue-red Anatidae design authority

The product palette and platform implementation rules are standardized in [ANATIDAE_DESKTOP_DESIGN_SYSTEM.md](ANATIDAE_DESKTOP_DESIGN_SYSTEM.md). That document supersedes earlier exploratory color-preset examples in this architecture. The production UI uses semantic white, blue and red tokens with separate light/dark surfaces; unrelated accent palettes are not part of the product identity.
