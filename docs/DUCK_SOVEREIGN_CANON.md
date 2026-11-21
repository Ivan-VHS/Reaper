# Shared desktop design canon

The four native GUI stacks remain distinct: Pytyliki/Win32, Reaper/Tk, OPlague/Tk, VentuSample/Qt.

| Token | HEX | Use |
|---|---|---|
| White | #FFFFFF | surface |
| Light | #F4F6FA | light background |
| River blue | #0039A6 | navigation/actions |
| Deep blue | #0A1E46 | text/dark surface |
| Signal red | #D52B1E | focus/accent |
| Critical red | #B51A10 | warning |

Target composition 60/25/15 (white/blue/red), not an exact pixel quota. Preserve WCAG contrast, keyboard focus, state text and native controls.


## Anatidae motion and surface extensions

The Pond reference contributes quiet white/blue/red washes (`#F8FAFC`, `#EFF6FF`, `#FEF2F2`) and an optional gold ornamental accent (`#D97706`). Gold is never used as a replacement for warning, error or success semantics. Serif display type is appropriate only for a welcome/hero title; body and control text remain native UI typography, and monospaced typography remains reserved for code, IDs and telemetry.

The paddle curve `cubic-bezier(0.22, 1.18, 0.36, 1)` and water curve `cubic-bezier(0.37, 0, 0.63, 1)` describe bounded feedback and optional brand artwork. They do not authorize persistent parallax or animation behind the editor or debugger. See [Anatidae motion constitution](ANATIDAE_MOTION_CONSTITUTION.md).
