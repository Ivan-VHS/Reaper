# Desktop UI Motion System — 2026

The desktop UI uses one accessible motion contract, implemented with native toolkit primitives. The reference motion lab is translated into native behavior instead of shipping its Tailwind/Google Fonts demo dependencies inside desktop applications.

## Motion modes

| Mode | Behavior |
| --- | --- |
| Normal | Restrained spring feedback, short pane transitions and dismissible status toasts |
| Expressive | Slightly longer emphasis transitions and a livelier, damped spring response |
| Reduced Motion | No spatial entrance; retained feedback is capped at 80 ms |
| Eco / Low-CPU | Suppresses decorative refresh and spatial motion; retained feedback is capped at 80 ms |

The spring uses a semi-implicit Euler step with a 32 ms frame clamp and two substeps. Stiffness, damping and stagger are bounded user preferences. The defaults are 240 / 22 / 55 ms; Expressive uses 340 / 14 / 75 ms.

## Interaction model

- Hover and press feedback stays on native controls. It must not move focus targets or change hit-area geometry.
- Notifications are native, dismissible toast surfaces; their entrance uses the spring solver and becomes static under Reduced Motion / Eco.
- Panel depth is expressed through spacing, border hierarchy and restrained elevation. Native Tk/Win32/Qt surfaces do not pretend to provide browser backdrop blur.
- Blue #0039A6 / navy #0B1F3A are used for navigation and calm feedback. Red #D52B1E / #B51A10 remains reserved for warnings, mutation and safety feedback. Decorative rainbow cycling, large-area flashing and uncontrolled parallax are not used.

## Accessibility and performance

Preferences are persisted across sessions. The system honors UI_REDUCED_MOTION and the native Windows preference. Animation is scheduled on the UI thread only; it must never block file operations, device inspection, generation, audio/DSP, worker threads, keyboard navigation or drag operations. BPM sync is only enabled when the application has a real tempo/transport source.
