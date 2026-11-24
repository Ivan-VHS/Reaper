# README and Visual Documentation Standard

**Scope:** Reaper README family, documentation indexes, diagrams and visual assets. Source code, tests, schemas and CI remain authoritative for product behavior.

## Publishing principles

- Lead with a factual one-line statement of the language, audience and primary workflow.
- Keep theme-aware hero, CI/license badges, navigation and the quick start near the top.
- Distinguish the Python compatibility reference runtime from the partial native C17 track everywhere.
- Label Windows screenshots, authored diagrams and planned UI concepts accurately.
- A documentation refresh is not a software release and must not invent a language version or a passing CI state.

## README sequence

Adaptive hero → one-line pitch → badges/navigation → maturity boundary → requirements and quick start → documentation-revival comparison → implementation matrix → visual overview → Mermaid architecture → real configuration/trust boundaries → repository map → verification and roadmap links → contribution/license.

## Hero assets

Use `assets/readme/hero-banner-light.svg` and `assets/readme/hero-banner-dark.svg` with the same viewBox/dimensions. Select with `<picture>` and `prefers-color-scheme`; keep accessible fallback alt text. SVG assets must be self-contained and use no external network resources.

## Screenshots and architecture visuals

- Use the original committed Studio capture in `assets/screenshots/` and link to its full-size file.
- Keep the workflow illustration under `assets/readme/`; do not call it a screenshot.
- Use a two-column, one-row visual grid where the screen width allows it.
- Add meaningful alt text and captions. Never depict a planned native compiler or IDE surface as implemented.
- If no verified capture exists, say so and use clearly labelled schematics.

## Technical accuracy

- Commands must match `pyproject.toml`, test discovery and CMake targets.
- Do not say native C17 has full parser/runtime/compiler parity.
- Describe LSP/DAP as local stdio services with their documented limitations.
- Document FFI and Node.js trust boundaries; do not invent an HTTP service, account, `.env` file or API credentials.
- Keep roadmap items in roadmap documents, not in the implemented feature table.

## Localization and acceptance

Keep English, Ukrainian, Russian and Simplified Chinese READMEs aligned in commands, status and architecture. Preserve exact CLI names and filenames. Before merge check links, Mermaid, image paths, language switch links and `git diff --check`.
