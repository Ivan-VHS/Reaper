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
