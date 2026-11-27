# Visual documentation and graphics contract

**Project:** Reaper · **Scope:** README, Markdown/MDX, architecture diagrams, screenshots, badges, typography and native IDE motion references.

This contract governs documentation presentation. A diagram or visual concept is not evidence that a runtime capability, renderer, shader, animation or feature is shipped.

## Documentation hierarchy

| Surface | Responsibility | Authority |
|---|---|---|
| `README.md` | Product identity, live Studio capture, current capabilities, commands and boundaries | Main branch and CI |
| `README.ru.md`, `README.uk.md`, `README.zh-CN.md` | Localized product entry points | Same capability status and release facts as English |
| `docs/README.md` | Canonical technical-documentation navigation | Existing files in `docs/` |
| `docs/VISUAL_DOCUMENTATION.md` | This visual and rendering contract | Architecture and UI contracts |
| `assets/` | Editable diagrams and real application captures | Original SVG source / desktop workflow |

Keep root `README.md` as the GitHub entry point. Do not maintain a competing `README.mdx`. Use `.mdx` only inside an actual configured docs site when reusable interactive components justify it.

## Markdown typography and page structure

- One H1 per page; use a short lead, ordered H2 sections and H3 subsections without heading-level skips.
- Prefer sentence-case headings, short paragraphs, descriptive link text and relative repository links.
- Put commands in fenced `sh` / `powershell` / `python` / `reaper` blocks; put identifiers, paths and shortcuts in inline code.
- Feature tables must distinguish **implemented**, **partial**, **planned**, **catalogued-only** and **not supported**. Registry size is not implementation evidence.
- Images require meaningful alt text. Captions must distinguish actual Studio screenshots from architecture maps, mock-ups and conceptual artwork.
- Do not use colour, badges, emojis, motion or visual effects as the only carriers of status or meaning.

## Visual system

### Vector graphics and geometry

Use static SVG for architecture maps, compiler/language flow, UI callouts and infographics. Preserve the SVG source, include `viewBox`, `<title>`, `<desc>`, clear typography and sufficient contrast. Avoid scripts, event handlers, animated SVG, external fonts, remote assets and `foreignObject` in GitHub-facing graphics. Use a consistent grid, aligned cards, restrained strokes and clear arrows; label interfaces and boundaries explicitly.

### Screenshots, rasterization and textures

The Windows 11 Studio screenshot must come from a real desktop build/run. Never present a designed SVG, browser prototype or synthetic window as a shipped IDE screenshot. Keep PNG for broad GitHub compatibility. WebP and AVIF are optional derivatives for a real documentation website, with the PNG source/fallback retained. Rasterize SVG from its master at the target density; do not upscale low-resolution artwork. Avoid textured or translucent backgrounds behind source text, diagnostics, debugger state or terminal output.

### Palette, lighting and composition

Follow the [UI/UX 2026 convergence contract](UI_UX_2026_CONVERGENCE.md): AETHER-ANAS white/blue/red, blue for normal navigation/focus, red for critical or destructive state, opaque readable work surfaces and native platform controls. Light, glow, gradients and transparency may be used sparingly in cover art, never to reduce code or data legibility.

### Motion and effects

README and architecture graphics remain static. The desktop UI follows [UI_MOTION.md](UI_MOTION.md) and the [Dak motion constitution](DAK_MOTION_CONSTITUTION.md). Reduced Motion and Eco override Expressive Motion. Do not move editor content, animate syntax or use parallax/particles behind precision panes. Never claim 60/120 FPS or zero jitter without reproducible measurements.

## Diagram, docs and publishing formats

| Format / tool | Use | Rule |
|---|---|---|
| GitHub Markdown + Mermaid | Small flowcharts, state diagrams and sequences | Preferred source-first choice for GitHub |
| PlantUML (`.puml`) | More detailed sequence/component/deployment diagrams | Commit source and a static SVG fallback |
| D2 (`.d2`) | Dense architecture and relationship maps | Use only where it clarifies the model |
| SVG infographic | Stable README/release fallback | Keep vector source editable and static |
| Markdown (`.md`) | Default portable repository documentation | Canonical format for README and docs |
| MDX (`.mdx`) | React/JSX-backed content components | Only in a configured site; not a README replacement |
| Docusaurus | Versioned guides, sidebars and docs IA | Optional adapter, not a current runtime dependency |
| VitePress | Markdown site with Vue enhancements | Optional adapter, not a current runtime dependency |
| Astro Starlight | Structured docs navigation and Markdown/MDX | Optional adapter, not a current runtime dependency |
| MkDocs Material | Docs site and navigation | Optional adapter; do not add without a publishing need |
| Shields.io | CI, license and release indicators | Point to real workflows and published facts only |
| GitHub Pages | Static docs publication | Requires an actual site build and deployment workflow |

GitHub Markdown remains the portable baseline. Choose one site generator only when publishing is needed; do not mix multiple framework conventions into the source docs. GitHub can render Mermaid fences in supported Markdown surfaces; keep a static SVG for other renderers and offline review.

## Reaper-specific visual boundaries

Reaper is an expression-oriented language with a Python compatibility-reference runtime, an active but incomplete C17 native track, and a Windows Tk Studio. Visuals must keep source and diagnostics primary. LSP/DAP diagrams must distinguish per-document language features from cross-file analysis (not claimed), and local IDE commands from cloud AI. Use native Tk transitions only; the browser-only HTML showcase effects are not a desktop implementation.

Keep the visual hierarchy editor-first: source text is primary; output, variables, debugger context and navigation are secondary but reachable. Preserve the visible distinction between Check, Run, Debug, Continue, Step and Stop. Show the Python runtime as the current compatibility reference; mark C17 as partial until conformance evidence exists. CODEX-66 catalogue entries must keep their individual maturity status.

## Review checklist

- [ ] Four README languages agree on current implementation status and boundaries.
- [ ] Studio image is a real desktop capture, with OS/build context.
- [ ] SVG includes title, description and viewBox; no script, remote asset or animation.
- [ ] Diagram source has a static fallback when GitHub or another host cannot render it.
- [ ] Motion and visual claims match native Tk implementation and tests.
- [ ] Badges represent actual CI, license or release facts.
- [ ] `docs/README.md` indexes the guide and every new canonical document.
- [ ] Relative links and code fences render correctly on GitHub.

## References

- [GitHub image and SVG rendering](https://docs.github.com/en/repositories/working-with-files/using-files/working-with-non-code-files)
- [GitHub Mermaid diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
- [Docusaurus Markdown and MDX](https://docusaurus.io/docs/markdown-features)
- [VitePress Markdown extensions](https://vitepress.dev/guide/markdown)
- [Astro Starlight authoring content](https://starlight.astro.build/guides/authoring-content/)
