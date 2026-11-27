# Reaper Studio UI/UX system

**Status:** implemented in the Tkinter desktop workbench. The language runtime and CLI remain UI-independent.

## Product surface

Reaper Studio is a programming workbench for the MOST/Reaper language. Its core layout is an editor with execution output and debugger context. The interface prioritizes source readability, keyboard access, clear run/check/debug states and fast inspection of variables and call stacks.

## Visual language

- **Platform-aware shell:** use the native Tk theme where available (Windows vista, macOS aqua); use a predictable cross-platform ttk theme elsewhere.
- **Controlled materials:** toolbars, editor, output and debugger views are opaque, stable surfaces. Liquid Glass/Mica is not faked with low-contrast overlays.
- **Light/dark/system modes:** use the View menu. System mode checks the platform appearance when detectable; REAPER_UI_THEME=light or dark can explicitly override it.
- **Editor-first hierarchy:** source text receives the strongest visual priority; output and variables remain secondary, reachable panes.
- **Dense but calm diagnostics:** tables, call stacks and runtime output use consistent row height, spacing and legible monospace typography.

## Platform adaptation

| Environment | UI direction | Implementation boundary |
|---|---|---|
| Windows | Native ttk base with Fluent-like spacing and blue focus/action states | Tkinter desktop shell |
| macOS | Aqua ttk base in light appearance; high-contrast fallback palette in dark appearance | No claim of full Liquid Glass integration |
| GNOME/Linux | Consistent ttk widgets and Libadwaita-inspired spacing and hierarchy | Not a GTK/Libadwaita application |
| Web dashboards | Not applicable to the editor shell | Metrics belong in dedicated reports, not decorative cards |

## Interaction and accessibility

- Preserve Ctrl+O, Ctrl+S, F5, Shift+F5 and F9 shortcuts.
- Keep Check, Run, Debug, Continue, Step and Stop as distinct operations.
- Make focus, active tabs, selected rows and output states distinguishable without color alone.
- Support long lines, horizontal scrolling, large output and multi-size windows.
- Keep reduced visual noise and stable contrast ahead of blur, glass or animated transitions.

## Shared visual contract

| Token | Light | Dark |
|---|---|---|
| Page | #F3F6FA | #101827 |
| Surface | #FFFFFF | #172337 |
| Text | #172337 | #EEF3FA |
| Muted | #5C6B80 | #A7B4C7 |
| Accent | #2563EB | #6EA8FE |
| Alert | #DC2626 | #F87171 |
| Editor | #FFFFFF | #111C2E |

## Related repositories

- [Pytyliki processor workstation](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/UI_UX_SYSTEM.md)
- [OPlague driver workbench](https://github.com/Ivan-VHS/OPlague/blob/main/docs/UI_UX_SYSTEM.md)

## Validation checklist

- System, light and dark modes apply without changing parser/runtime behavior.
- Source editing, output, variable inspection and call-stack navigation remain intact.
- Keyboard shortcuts continue to invoke their original commands.
- Text and selection remain readable in both palettes.

## 40026 Codex

The normative six-cycle engineering contract is maintained in [UI/UX Codex 40026](UI_UX_CODEX_40026.md). Theme palettes now expose semantic Success/Warning/Error/Info roles and are rejected when required WCAG AA text pairs fall below 4.5:1. Automated checks cover every supported palette. Full keyboard walkthrough, 200% scaling and long-session ergonomics remain release-level manual checks.

## UI/UX 2026 convergence

See [UI_UX_2026_CONVERGENCE.md](UI_UX_2026_CONVERGENCE.md) for semantic tokens, accessibility targets, responsive behavior and motion budgets. Existing Reaper editor and atmospheric theme profiles remain supported.

## Dak desktop visual refinement

The Studio shell carries a restrained 5 px white-blue-red identity band. The code editor, syntax tokens, caret, selection and line-number gutter must follow the active light/dark palette together; no fixed light-theme labels or gutter colors may leak into dark mode. Keep the editor the primary surface and retain all keyboard shortcuts and runtime behavior.
