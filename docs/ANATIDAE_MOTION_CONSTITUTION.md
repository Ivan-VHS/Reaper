# Anatidae Motion Constitution — shared desktop profile

This profile translates the supplied Pond / DAK Constitution visual language into the four native workstations. It is a design-system integration, not a product rename: each application keeps its own information architecture, product vocabulary and toolkit.

## Visual tokens

| Token | Value | Meaning |
|---|---|---|
| Feather white | `#FFFFFF` | primary surface |
| Mist | `#F8FAFC` | quiet background |
| Blue wash | `#EFF6FF` | calm, navigational grouping |
| Red wash | `#FEF2F2` | explicit warning or action grouping |
| River blue | `#0039A6` | primary navigation and actions |
| Deep blue | `#0A1E46` | strong text and dark surfaces |
| Signal red | `#D52B1E` | focus / active signal |
| Critical red | `#B51A10` | destructive or safety-critical state |
| Gold | `#D97706` | optional ornamental accent only |

The white / blue / red composition target remains 60 / 25 / 15, not a measured quota. Red never becomes a generic hover colour for every control, and gold never replaces a semantic status. Keep focus indicators, text labels and WCAG contrast independent of colour.

## Type and surfaces

Use the native application font for controls and body text. A serif display face may be used for a product hero or welcome panel; a monospaced face belongs to code, IDs, values and telemetry. Do not fetch remote fonts at runtime in offline desktop products. Prefer opaque native surfaces, restrained borders and shadows; backdrop blur is optional browser decoration, not a desktop dependency.

## Motion language

| Token | Curve / budget | Native meaning |
|---|---|---|
| Paddle | `cubic-bezier(0.22, 1.18, 0.36, 1)` | soft, quick acknowledgement with a bounded overshoot |
| Water | `cubic-bezier(0.37, 0, 0.63, 1)` | slow, symmetric drift for decorative brand elements |
| Direct acknowledgement | 0–40 ms | immediate action; never wait for animation |
| Hover / focus / state | 80–140 ms | short colour, opacity or border feedback |
| Pane / tab transition | 160–240 ms | restrained opacity or layout transition |
| Hero / scene transition | 260–380 ms | optional, non-critical presentation only |
| Reduced motion | at most 80 ms | no spatial motion; retain only essential acknowledgement |

The paddle curve is clamped to each native property's legal range. It must not make focus, selection, warning, progress or data updates ambiguous.

## Pond-specific motifs

The supplied dak bob, tail waggle, wave glide, ripples, accent particles, floating feathers and parallax layers are treated as a reusable *brand-motion vocabulary*:

- Use bobbing and tail motion only for a mascot or illustration in a welcome, empty or showcase surface. Keep the movement small (about 6 px and 2 degrees).
- A water ripple may acknowledge one deliberate primary action; it must not obscure labels, values, keyboard focus or hit targets.
- Feather particles and voice bursts are optional showcase effects, not permanent UI chrome. They require an explicit pause/disable path.
- Parallax is restricted to a low-contrast landing/hero background, with a small bounded offset. Never place moving layers behind editors, tables, plots, device inventories, logs or precision controls.
- DAK-specific terminology and illustrations are not forced into product features. Reuse the physical motion principles, not the pond's fictional legal content.

## Accessibility, performance and lifecycle

1. Operating-system reduced-motion settings and `UI_REDUCED_MOTION` take precedence.
2. Reduce Motion removes parallax, bobbing, particles and spatial movement; any retained transition is at most 80 ms.
3. Eco / Low-CPU Visuals suppresses all ambient effects and secondary refresh work.
4. A pause control is mandatory wherever ambient animation is offered.
5. Animation runs on the UI thread only, is cancelled when its window/widget is destroyed and never blocks work queues.
6. UI motion must never run inside time-critical callbacks, data buffers, background workers, benchmarks, device scans, archive inspection or compiler/runtime execution.

## Native implementation map

- **Pytyliki / Win32:** native startup transition only; Expressive may use a short vertical glide. No continuous background timer or animated performance controls.
- **Reaper / Tk:** bounded UI-thread spring controller; optional showcase effects stay out of editor and debugger panes.
- **OPlague / Tk:** persisted Expressive paddle easing; inventory and evidence panes remain still and opaque.
- **VentuSample:** maintains its application-specific motion behavior in its own repository; it is not a Reaper runtime module.

This file is the shared visual/motion reference. Product-specific contracts in `docs/UI_MOTION.md` remain authoritative for what is actually enabled in each application.


## Motion Constitution v2026 precedence

The normative shared motion, layout and telemetry contract is [Motion Constitution v2026](MOTION_CONSTITUTION_V2026.md). This design document supplies visual-language guidance; it does not override the canonical token ranges or product-specific implementation status.

Shared tokens: `--ease-spring`, `--ease-snappy`, `--motion-scale` (0.4–2.2) and normalized `--spring-stiffness` (0.7–1.4). Operating-system reduced-motion and `UI_REDUCED_MOTION` take precedence; nonessential spatial/ambient motion is removed and the underlying state change is retained. Light/dark parity, keyboard focus and high-DPI readability apply to every supported visual state.

The 2×2 overview and focus scene are showcase layout targets. SVG/Canvas or native-paint graphics must be driven by real model values, expose units and textual equivalents, and distinguish unknown, stale and error states. Product-specific `docs/UI_MOTION.md` remains authoritative for shipped native behavior and safety boundaries.
