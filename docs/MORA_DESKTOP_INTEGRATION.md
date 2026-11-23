# Mora desktop integration — Reaper Studio

Reaper Studio joins the Mora workspace as the programming and language-tooling application. The Reaper runtime, CLI, LSP/DAP services and C17 track remain independent of Mora.

## Workspace contract

- Manifest: mora-app.json, version 1.
- Launch entry point: reaper_desktop.py, using the current Python interpreter.
- Window model: a separate Tk native window managed by the operating system.
- Theme hand-off: MORA_THEME_MODE=dark or light.
- Local execution only; Mora does not add an HTTP service or remote execution path.

The canonical manifest schema and host behavior are documented in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/MORA_DESKTOP.md).

## Shared visual language

When Reaper Studio is launched by Mora, the inherited theme is applied before the Studio widgets are created. The shared modes reuse the project's existing semantic palette:

| Role | Dark | Light |
|---|---|---|
| Page | #071A2D | #F4F8FD |
| Surface | #0F2A45 | #FFFFFF |
| Text | #E8EDF2 | #122C45 |
| Primary | #70A5FF | #004E98 |
| Signal | #FF7B86 | #B5122D |

The shell's environment value is a startup default. An explicit theme selected inside Studio still takes precedence for that session. Reaper retains its editor-first hierarchy, keyboard commands, diagnostics, output and debugger panes.

## Product boundaries

Mora launches the existing Studio entry point; it does not embed a browser editor, execute a project on behalf of the user, modify source files or alter the language runtime. Python remains the executable compatibility reference and native C17 remains a separately documented partial track.

## Verification

Run the existing Reaper suite after the UI theme change:

    python -m compileall -q reaper tests
    python -m unittest discover -s tests -v

The shared visual contract does not replace the UI/UX requirements in UI_UX_SYSTEM.md or the release-level keyboard, DPI and accessibility review.
