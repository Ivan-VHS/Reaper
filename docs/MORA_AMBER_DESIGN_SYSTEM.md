# Mora Noir theme profile — Reaper Studio

**Maintainer:** Ivan-VHS

The default Reaper Studio profile uses the shared Imperial Noir surface foundation while preserving Reaper's own blue action/navigation language and red critical-action language. Light, Dark, Dawn, Sunset and Night remain available. The profile is saved through local user preferences and can be selected with `REAPER_UI_THEME=mora`.

## Palette

| Role | Value |
|---|---|
| Workspace | `#050505` |
| Editor / panel | `#101010` |
| Elevated panel | `#181818` |
| Main text | `#FFFFFF` |
| Supporting text | `#E5E5E5` |
| Muted text | `#A6A6A6` |
| Main action / navigation | `#70A5FF` |
| Hover / focus | `#8AB6FF` |
| Critical | `#FF7B86` |
| Selection | `#244F82` |
| Structural edge | `#3A3A3A` |

The code editor, debugger, terminal output and diagnostics keep opaque, high-contrast surfaces. Blur, parallax and ambient movement are not added over code. The UI does not alter source content, runtime behavior, debugger timing or build output.

## Motion and layout

The editor remains the primary visual anchor. Use stable split layouts, clear pane boundaries and predictable vertical spacing. The existing motion controller remains authoritative; Reduced Motion and Eco settings suppress nonessential movement.

## Status language

Success, warning, error and information use distinct semantic colors with explicit text/icon labels. No status is communicated by hue alone.

## Verification

The canonical color validator checks every semantic text pair against the UI/UX 40026 contrast contract. Keyboard, high-DPI and physical-display review remains part of release acceptance.
