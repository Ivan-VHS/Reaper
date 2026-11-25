# UI/UX 2026 — shared product interface contract

**Maintainer:** Ivan-VHS · **Product:** Reaper Studio  
**Design language:** AETHER-ANAS / Anatidae — consistent white/blue/red identity adapted to native platform behavior.

This is an implementation contract for an operational desktop tool. The next useful task should be obvious, information should stay legible, and visual feedback must never interrupt code execution or debugging.

## Semantic palette

| Token | Light | Dark | Role |
|---|---|---|---|
| bg | #F4F8FD | #071A2D | Workspace |
| surface | #FFFFFF | #0F2A45 | Main panels and editors |
| elevated | #EAF1FA | #173A5E | Secondary surfaces |
| fg | #122C45 | #E8EDF2 | Primary text |
| secondary | #314B66 | #D0DCE8 | Supporting text |
| muted | #4D6177 | #B3C4D6 | Hints and metadata |
| blue | #004E98 | #70A5FF | Actions and navigation |
| blue_hover | #1A5FDB | #8AB6FF | Hover and focus |
| on_blue | #FFFFFF | #071A2D | Text on blue |
| red | #B5122D | #FF7B86 | Critical/destructive states |
| red_hover | #9C1026 | #FF9AA2 | Critical-action hover |
| on_red | #FFFFFF | #071A2D | Text on red |
| border | #CAD8E8 | #31516F | Boundaries |
| focus | #1A5FDB | #8AB6FF | Keyboard focus |
| selection | #D9E8FF | #244F82 | Selected content |
| selection_fg | #122C45 | #FFFFFF | Text on selection |
| disabled | #6B7C90 | #9BAFC4 | Disabled text |

Blue is the normal action/navigation/focus language. Red is reserved for critical actions and safety. Use opaque work surfaces rather than decorative blur.

## Hierarchy and density

- Editor-first: source text is primary; output, variables and debugger panes remain secondary but quickly reachable.
- Keep Check, Run, Debug, Continue, Step and Stop as distinct operations.
- Use an 8 px spacing rhythm, persistent labels and explicit units.
- Prefer 40–44 px action targets; dense tables may use 34–36 px rows where readable.
- Use native system fonts for controls and monospace typography for source and diagnostics.

## Accessibility and input

- Give interactive controls meaningful accessible names and visible keyboard focus.
- Preserve Ctrl+O, Ctrl+S, F5, Shift+F5 and F9, plus native text-selection and navigation behavior.
- Target 4.5:1 contrast for normal text and 3:1 for focus; aim for 7:1 for primary body text where practical.
- Reduced Motion overrides Expressive Motion; Eco suppresses nonessential visual work. Honor native OS settings and `UI_REDUCED_MOTION`.
- Never use color, hover or motion as the only signal.

## Motion 2026

| Event | Timing |
|---|---:|
| Direct acknowledgement | 0–40 ms |
| Hover/focus/state | 80–140 ms |
| Pane transition | 160–240 ms |
| Context transition | 260–380 ms |
| Reduced-motion replacement | ≤80 ms |

Expressive Motion may scale supported transitions by 1.35×, capped at 380 ms. Reduced Motion removes spatial movement and caps retained fades at 80 ms; Eco follows the same conservative path. Animation remains on the UI thread and never changes runtime, worker, build or debugger timing.

## Responsive and high-DPI

Reflow panes rather than hide essential actions. Validate narrow/wide layouts, keyboard-only operation, and 100%, 125%, 150% and 200% scaling. Manual monitor review remains an acceptance item until performed.

## Product-specific implementation

Reaper Studio is an editor-first Tkinter IDE. Source readability, output, variable inspection, debugger context and keyboard-first commands outrank decorative dashboards. Preserve Check / Run / Debug distinctions and shortcuts. Apply shared tokens to ttk and classic Tk surfaces. Motion must not affect language runtime, workers, embedded builds or debugger paths.

## Engineering references

- [Qt Accessibility](https://doc.qt.io/qt-6/accessible.html) · [Qt High DPI](https://doc.qt.io/qt-6/highdpi.html)
- [WCAG 2.2 Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html)
- [Microsoft Windows app design](https://learn.microsoft.com/windows/apps/design/)

These references define targets, not unverified test claims.


## Reaper brand-preserving adoption

Dark and default Studio surfaces use `#050505`, `#101010` and `#181818`.
Reaper retains blue for actions/navigation and red for critical operations. Keep
the editor opaque and source-first; do not place blur, parallax or ambient motion
over source, diagnostics or debugger state.
