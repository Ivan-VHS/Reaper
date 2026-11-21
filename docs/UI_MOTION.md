# Desktop UI motion contract

The desktop UI follows the AETHER-ANAS white/blue/red motion contract. Motion is functional feedback, not ambient decoration.

## Timing and curves

| Interaction | Budget |
| --- | ---: |
| Direct control acknowledgement | 0–40 ms |
| Hover, focus and state changes | 80–140 ms |
| Pane and graph reflow | 160–240 ms |
| Scene/preset transitions | 260–380 ms |
| Reduced-motion replacement | no more than 80 ms |

The default easing is `cubic-bezier(0.2, 0.8, 0.2, 1)`; click/transient feedback uses `cubic-bezier(0.05, 0.9, 0.2, 1)`. Linear motion is reserved for time/phase indicators. No large-area strobing, uncontrolled parallax or decorative rainbow cycling is permitted.

## Semantic colour

- Blue `#0039A6` / navy `#0B1F3A`: navigation, focus paths and calm state.
- Red `#D52B1E` / `#B51A10`: generation, mutation, clipping and safety events only.
- Signal animations must encode a measured value or state.

## Accessibility and performance

Preferences are persisted separately from theme settings:
- **Reduce Motion** caps any retained transition at 80 ms and removes spatial/window movement.
- **Eco / Low-CPU Visuals** suppresses nonessential visual effects and secondary refresh work.
- **Sync to Transport / BPM** is enabled only when a real project transport/tempo source exists. It must not pretend to sync when the host has no transport.

All animation work stays on the UI thread and must never block audio/DSP, generation, worker, keyboard or drag operations. This application has no audio transport; BPM sync is therefore intentionally unavailable in this UI.
