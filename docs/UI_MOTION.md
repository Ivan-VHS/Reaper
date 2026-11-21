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
- **Sync to Transport / BPM** is enabled only when a real project transport/tempo source exists. Reaper Studio has no audio transport, so BPM sync remains unavailable.

All animation work stays on the Tk UI thread and must never block execution, embedded builds, debug pauses, worker, keyboard or drag operations.


## Anatidae / Pond Motion translation

Reaper's existing `Spring1D` controller provides the expressive paddle response using a bounded mass-spring-damper solver. The shared tokens are `PADDLE_EASING = cubic-bezier(0.22, 1.18, 0.36, 1)` and `WATER_EASING = cubic-bezier(0.37, 0, 0.63, 1)`; the former describes the short, damped control response, while the latter is reserved for optional showcase artwork. Reduce Motion and Eco continue to override Expressive Motion and cap retained transitions at 80 ms.

Duck illustrations, parallax, particles and water ripples are optional landing/showcase motifs only. They are not placed behind the editor, debugger, project tree, diagnostics or terminal output. The native IDE keeps opaque work surfaces, predictable focus paths and all animation on the Tk UI thread.

See the [shared Anatidae motion constitution](ANATIDAE_MOTION_CONSTITUTION.md).
