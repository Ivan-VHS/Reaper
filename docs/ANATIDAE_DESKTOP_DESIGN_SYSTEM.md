# Anatidae Desktop Design System — Reaper Studio

**Status:** implemented Tk theme baseline and adaptive command bar; full pane orchestration, locale completion and physical 8K regression remain future acceptance work. This specification is the authoritative white-blue-red UI contract for Reaper Studio.

## 1. Design intent

Reaper Studio is a flow-first programming environment. The editor remains the primary surface; Check, Run and Debug are always easy to find; Output, Variables and Call Stack remain inspectable without obscuring source context. Visual polish must not imply that the staged native C17 frontend is a complete interpreter or that specified language features are already executable.

## 2. White-blue-red tokens

| Semantic token | Light theme | Dark theme |
|---|---|---|
| Workspace | \`#F4F8FD\` | \`#071A2D\` |
| Surface / editor | \`#FFFFFF\` | \`#0F2A45\` |
| Elevated surface | \`#EAF1FA\` | \`#173A5E\` |
| Primary text | \`#122C45\` | \`#E8EDF2\` |
| Secondary text | \`#314B66\` | \`#D0DCE8\` |
| Muted text | \`#4D6177\` | \`#B3C4D6\` |
| Primary blue | \`#004E98\` | \`#70A5FF\` |
| Blue hover | \`#1A5FDB\` | \`#8AB6FF\` |
| Action / danger red | \`#B5122D\` | \`#FF7B86\` |
| Red hover | \`#9C1026\` | \`#FF9AA2\` |
| Border | \`#CAD8E8\` | \`#31516F\` |
| Focus | \`#1A5FDB\` | \`#8AB6FF\` |
| Selection | \`#D9E8FF\` | \`#244F82\` |

No unrelated green, yellow, violet or teal accent is introduced. Syntax/status meaning must remain readable in monochrome and must not rely on hue alone. Body text targets 7:1 contrast; actionable labels target at least 4.5:1. The Python theme module exposes a WCAG contrast helper and tests for both palettes.

## 3. Controls and typography

- Primary Run action uses blue fill and contrasting text. Stop uses the red danger style. Supporting commands use a calm surface with blue text.
- Buttons and notebook tabs use generous padding and visible focus. Prefer 44px interactive height; do not reduce hit areas to preserve a dense toolbar.
- Segoe UI is used for UI labels; Consolas is reserved for Reaper source and runtime output. Keep code editor text independent from UI theme sizing.
- Use 8pt-aligned spacing: 8/16/24/32 logical px. Keep editor and output scrollable; do not force long code lines to wrap.
- Theme changes update ttk controls, editor/output Text widgets, Listbox, menus, tables and selection in a single operation.

## 4. Adaptive workspace and 8K

The command bar is split into file/theme actions and execution/debug actions, so it can occupy two short rows rather than overflow a narrow window. Editor and inspector continue to resize through the Tk paned window. The current vertical pane arrangement preserves code-first reading; future compact mode may collapse inspectors into tabs, while wide mode may add a symbol navigator and semantic inspector.

The app requests Per-Monitor V2 DPI awareness before creating Tk. Tk logical geometry follows OS scaling. Physical 8K is not a reason to shrink fonts or create giant unstructured editor lines. 7680×4320 at 100–300% still needs real-device visual regression and per-monitor movement checks before certification.

## 5. Materials, motion and accessibility

Tk uses its controllable \`clam\` widget theme for consistent semantic tokens while the operating-system window frame remains native. The UI uses opaque surfaces and layered blue/white contrast. Mica/Acrylic, true vector iconography and shared-element motion are not claimed by the current Tk shell.

The current Studio is intentionally motion-light. No decorative animations run; this is the reduced-motion-safe baseline. Keyboard shortcuts (Ctrl+O, Ctrl+S, F5, Shift+F5, F9), visible focus, logical tab order, accessible command names and source-linked diagnostics remain part of the contract.

## 6. Platform implementation ledger

| Area | Current implementation |
|---|---|
| Theme | \`reaper/ui_theme.py\`: light/dark semantic tokens, contrast calculation, ttk styles and native Text/Listbox/Menu repaint |
| Persistence | Theme preference stored as versioned JSON under the user config directory |
| Theme control | Toolbar toggle switches Light/Dark and persists the selected mode |
| Responsive toolbar | Two-row file/theme and execution/debug command groups |
| DPI | Per-monitor DPI awareness requested before Tk initialization |
| Data safety | Python reference runtime remains authoritative; native C17 status is still staged |
| Not claimed | CSS container queries, Mica/Acrylic, animated transitions, full locale parity or certified 8K screenshots |

## 7. Visual review capture plan

Capture the running Studio in both themes; the two-row command bar at 780px and 1120px widths; source editor plus Output; Variables and Call Stack tabs; keyboard focus; selected tree rows; and an 8K/HiDPI test at OS scaling. Illustrative previews must be labelled and cannot substitute for live captures.

## 8. Release checklist

- [ ] Theme token completeness and contrast tests pass.
- [ ] Theme switch updates every ttk and classic Tk text surface.
- [ ] Theme choice survives restart.
- [ ] Toolbar remains usable at the minimum window width.
- [ ] Editor, Output, Variables and Call Stack remain available.
- [ ] Focus, keyboard shortcuts and reduced-motion baseline work.
- [ ] UI does not misrepresent planned/native language features as implemented.
- [ ] Real-device 8K screenshots and per-monitor movement checks are completed before certification.


## 9. Anatidae identity grammar — lexical and visual expansion

### 9.1 Design intent

The supplied Anatidae word family is a design vocabulary for approachability, recognition, movement and coherent surfaces. It is **not** an instruction to turn technical software into a children's product. Do not scatter duck illustrations, quack jokes or diminutive words through command names, diagnostics, settings, reports or safety notices. Product copy stays precise and professional.

### 9.2 Consolidated lexical matrix

Repeated forms are normalized; spelling variants are retained here as creative source terms rather than duplicated interface labels.

| Design role | Source vocabulary | Product interpretation |
|---|---|---|
| First contact and guidance | Утёнок, Утёныш, Утеныш, Уточёнок, Утёночек, Утеночек, Утёнушка, Утюша, Утя, Утюня, Утюняш, Утюняшка, Утяшка, Кряквёнок, Крякушонок, Крякалыш, Птенчик, Птенец, Птеныш, Пухляш, Пушистик, Пернатик, Крылыш, Водоплавчик | Welcoming first-run flow, plain-language empty states, clear defaults, progressive disclosure and compact help |
| Product identity and recognition | Утка, Уточка, Крякуша, Кряква, Кряквашка, Птица, Пташка, Пернатая, Крылатая | A recognizable abstract brand mark and consistent navigation language; never a mascot-heavy UI |
| Shape, surface and motion | Пуховичок, Пёрышко, Лапчатая, Прудовая, Озерная, Водоплавающая, Водяная птица | Softly layered surfaces, fine feather-like separators, stable touch targets, subtle waterline/ripple cues and responsive flow |
| Experimental vocabulary only | Крякозябра, Крякальщица | Internal creative references only; do not expose them as production feature names or status labels |

### 9.3 Shared visual grammar

- **Water:** use calm, continuous page-to-panel hierarchy and subtle progress/wave cues. Water is a compositional metaphor, not a translucent effect.
- **Plumage:** use restrained fine-line dividers, compact grouped metadata and consistent icon strokes. Never add noisy feather textures behind text or data.
- **Wing:** use directional alignment, clear action grouping and predictable focus travel. Do not use decorative flight animations.
- **Webbed-foot tactility:** preserve generous hit targets, stable controls and visible pressed/focused states.
- **Young-bird vocabulary:** translate it into a first-run/quick-start experience, progressive disclosure and helpful empty states—not infantilized copy.
- **Pond and lake:** retain the established semantic white/blue/red palette and opaque light/dark surfaces. No teal, amber, green or violet accent palette is introduced by this metaphor.
- Keep the shared 8pt spacing rhythm, 44 logical px preferred action targets, readable text measure, keyboard operation and reduced-motion behavior.

### 9.4 Cross-product expression

The shared identity is deliberately quiet; each product expresses it through its own work:

- **Pytyliki:** contained instrument panels, stable measurement surfaces and clearly separated processor, source-review and DSP workbenches.
- **Reaper Studio:** a source-first flow surface, directional command grouping and inspectable output/debug panes that never displace the editor.
- **OPlague:** layered evidence from concise summary to exact identifiers and package details; provenance and read-only boundaries remain more visible than decorative status.
- **VentuSample:** rhythmic grid and phrase-oriented grouping, with waveform/sample-chop cues and deterministic progress. Do not imply live playback, real-time rendering or hardware monitoring that the application does not provide.

### 9.5 Acceptance

- The brand is recognizable without a cartoon duck or a background illustration.
- The lexical source remains a design metaphor; all production labels stay technically meaningful.
- Existing light/dark tokens, accessibility, safety limits, data contracts and keyboard behavior remain authoritative.
- Motion is state-led, nonessential and disabled or minimized under reduced-motion settings.
- A visual refresh cannot promote a planned capability to implemented status.


### Reaper Studio application profile
The editor is the stable centre of the flock: keep source text dominant, and arrange Check / Run / Debug as a short directional command group. Output, Variables and Call Stack are supporting wings that can be inspected without covering source context. A first-run path should lead from Open → Check → Run → Inspect, while preserving the truth that Python is the compatibility reference and the native C17 path is partial.
