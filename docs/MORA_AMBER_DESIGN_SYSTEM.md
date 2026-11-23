# Mora Amber theme profile — Reaper Studio

**Maintainer:** Ivan-VHS

Reaper Studio's existing Mora theme identifier now resolves to the shared amber/sand visual profile. Light, Dark, Dawn, Sunset and Night remain available. The theme is saved through the existing user preferences and may be selected with `REAPER_UI_THEME=mora`.

## Palette

| Role | Value |
|---|---|
| Workspace | `#211913` |
| Editor / panel | `#33261D` |
| Elevated panel | `#493326` |
| Main text | `#FFF3E2` |
| Supporting text | `#E7D2B8` |
| Muted text | `#C4A98A` |
| Main action | `#D58B3D` |
| Hover / focus | `#EAA653` / `#F3C16B` |
| Critical | `#B64A40` |
| Selection | `#60442E` |
| Structural edge | `#75543A` |

The code editor, debugger, terminal output and diagnostics keep opaque, high-contrast surfaces. No blur, parallax or ambient movement is added over code.

## Motion and layout

The editor remains the primary visual anchor. Use stable split layouts, clear pane boundaries and predictable vertical spacing. The existing motion controller remains authoritative; reduced-motion and eco settings suppress nonessential movement.

## Verification

The canonical color validator recognizes the Mora Amber palette. UI theme tests cover warm text, action and critical colors. Keyboard, high-DPI and physical-display review remains part of release acceptance.
