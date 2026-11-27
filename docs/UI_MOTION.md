# Desktop UI motion contract

The Reaper Studio desktop UI follows the AETHER-ANAS white/blue/red contract, extended by the shared Anatidae / Pond Motion profile. Motion is functional feedback, not ambient decoration. The 2026 Motion Lab concepts are implemented as native Tk transitions; browser-only CSS effects are not copied into the desktop IDE.

## Timing and curves

| Interaction | Budget |
| --- | ---: |
| Direct control acknowledgement | 0–40 ms |
| Hover, focus and state changes | 80–140 ms |
| Pane and graph reflow | 160–240 ms |
| Scene/preset transitions | 260–380 ms |
| Reduced-motion replacement | no more than 80 ms |

The default easing is `cubic-bezier(0.2, 0.8, 0.2, 1)`; click/transient feedback uses `cubic-bezier(0.05, 0.9, 0.2, 1)`. Window presentation uses a bounded mass-spring-damper solver (semi-implicit Euler, capped 32 ms delta, two substeps). Expressive Motion increases the spring response and duration by 1.35x, capped at 380 ms.

## Modes and visual language

- **Normal** uses restrained spring feedback and the default duration tokens.
- **Expressive Motion** uses a stronger spring response for window/panel presentation.
- **Reduce Motion** removes spatial movement and caps any retained transition at 80 ms.
- **Eco / Low-CPU Visuals** suppresses nonessential effects and applies the same 80 ms ceiling.
- Reduce Motion and Eco always override Expressive Motion.

Blue `#0039A6` / navy `#0B1F3A` mark navigation, focus paths and calm state. Red `#D52B1E` / `#B51A10` is reserved for generation, mutation, clipping and safety events. The Liquid Glass / portal reference is translated into restrained solid surfaces, border highlights and clear focus states. Cursor magnets, uncontrolled 3D tilt, full-screen mesh animation and scroll parallax are intentionally excluded from the code editor and precision tool panes.

## Accessibility and performance

Preferences are persisted separately from theme settings, and old preference files remain valid (the new Expressive Motion flag defaults to off).

- **Reduce Motion** also respects the native operating-system setting and `UI_REDUCED_MOTION`.
- **Eco / Low-CPU Visuals** suppresses nonessential visual effects and secondary refresh work.

All animation work stays on the Tk UI thread and must never block execution, embedded builds, debug pauses, worker, keyboard or drag operations.


## Anatidae / Pond Motion translation

Reaper's existing `Spring1D` controller provides the expressive paddle response using a bounded mass-spring-damper solver. The CSS-style paddle/water values are stable design tokens; they describe the intended feel, while the native spring solver remains the actual Tk implementation. The shared tokens are `PADDLE_EASING = cubic-bezier(0.22, 1.18, 0.36, 1)` and `WATER_EASING = cubic-bezier(0.37, 0, 0.63, 1)`; the former describes the short, damped control response, while the latter is reserved for optional showcase artwork. Reduce Motion and Eco continue to override Expressive Motion and cap retained transitions at 80 ms.

Decorative illustrations, parallax, particles and water ripples are optional landing/showcase motifs only. They are not placed behind the editor, debugger, project tree, diagnostics or terminal output. The native IDE keeps opaque work surfaces, predictable focus paths and all animation on the Tk UI thread.

See the [shared Anatidae motion constitution](ANATIDAE_MOTION_CONSTITUTION.md).


## Motion Constitution v2026 mapping

The shared token, accessibility and documentation source is [Motion Constitution v2026](MOTION_CONSTITUTION_V2026.md). This native contract remains the authority for what this application actually ships.

- Canonical easing names: `--ease-spring` (bounded paddle response) and `--ease-snappy` (predictable state transitions); native curves are mapped in this document.
- Canonical scale envelope: `--motion-scale` = 0.4×–2.2× and spring stiffness multiplier 0.7–1.4. These are shared design tokens; they are not exposed as user controls unless the application UI and runtime explicitly implement them.
- Reduced Motion: OS preference and `UI_REDUCED_MOTION` take precedence; spatial/ambient motion is removed, state changes remain immediate, and only essential feedback may retain a fade of up to 80 ms.
- Theme/layout parity: light/dark themes, keyboard focus and high-DPI layouts remain required. 2×2 overview and focus-scene are showcase layout targets, not a claim that this native product already provides those views.
- Telemetry graphics: SVG/Canvas/native-paint charts must bind to sourced model values, show units and an accessible textual equivalent, and expose stale/error/unknown states. Demo data must be labelled.

### Product-specific maturity

Reaper Studio has native Tk spring presentation, persisted Reduce Motion/Eco/Expressive preferences, editor/debugger and local LSP/DAP tooling. CODEX-66 and the language service are local; they are not a cloud AI agent or streamed AI Diff. AST fold and diff timeline states must be exposed only where the corresponding editor model exists. No motion may delay runtime execution, debugging or language-service work.
