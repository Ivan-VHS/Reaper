# Disney Motion System — Reaper Studio

This repository adopts a product-focused interpretation of the twelve animation principles described by Frank Thomas and Ollie Johnston. The principles are a design vocabulary, not a mandate to make every control move. Motion must explain state, preserve orientation, and respect the user's time.

## Product contract

- Motion is feedback, never a prerequisite for understanding or operating the application.
- Keep the product's existing visual identity, layout, typography, and platform conventions.
- Use native Python / Tkinter desktop workbench behavior; do not introduce a web animation runtime or a new UI framework.
- Prefer short, interruptible transitions. Cancel or replace an in-flight transition when a newer user action supersedes it.
- Do not animate security, device, filesystem, processor, driver, or other safety-critical operations in a way that implies an operation has completed before its actual result is known.
- Respect system reduced-motion preferences and the `UI_REDUCED_MOTION=1` override. In reduced mode, preserve state changes and status text while removing spatial movement, bounce, zoom, and decorative motion.

## Shared timing tokens

| Token | Duration | Use |
|---|---:|---|
| instant | 0 ms | Reduced motion, immediate state |
| micro | 100 ms | Press, hover, focus feedback |
| fast | 140 ms | Small control or icon transition |
| standard | 180 ms | Menu, disclosure, compact panel |
| spatial | 240 ms | Window, tab, or workspace transition |
| emphasis | 280 ms | Success/error feedback; only when useful |

Default easing: `ease-out` for entry, `ease-in` for exit, `ease-in-out` for repositioning. Use linear timing only for continuous progress indicators. Keep stagger intervals at 20–30 ms and cap the total stagger window at 120 ms.

## The twelve principles translated to UI

1. **Squash and stretch** — restrained press feedback and elastic overscroll; never deform text or data.
2. **Anticipation** — hover/focus previews and clear affordances before a consequential action; never delay the action.
3. **Staging** — one dominant focus; dim or quiet secondary surfaces only when a modal task requires it.
4. **Follow-through and overlap** — short, bounded stagger for related content; parent motion leads child motion.
5. **Slow in and slow out** — consistent easing curves for entry, exit, and repositioning.
6. **Arcs** — optional curved trajectories for spatial transitions; preserve straight, predictable movement in dense workspaces.
7. **Secondary action** — supporting icon or status feedback that reinforces, but never competes with, the primary result.
8. **Timing** — use the tokens above; input response must remain immediate and transitions must be interruptible.
9. **Exaggeration** — reserve stronger emphasis for meaningful success, validation errors, and critical alerts.
10. **Solid drawing** — preserve geometry, alignment, clipping, layer order, focus rings, and readable contrast throughout every frame.
11. **Appeal** — motion should match the product's established character and feel deliberate rather than ornamental.
12. **Consistent appeal / staging across scenes** — treat the complete user journey as one coherent motion language; do not animate isolated screens with unrelated rules.

## Component behavior

- **Buttons and toggles:** immediate pressed/focused state; optional 1–2% scale or equivalent native feedback, with no layout shift.
- **Menus and disclosures:** reveal from their trigger with a short opacity/position transition; preserve keyboard focus and Escape behavior.
- **Dialogs:** establish a clear focus boundary; restore focus to the invoking control when closed.
- **Tabs and navigation:** communicate continuity between the selected destination and its content; do not animate large distances in dense tools.
- **Lists and tables:** avoid per-row cascades for large datasets; update data immediately and use restrained change indicators.
- **Charts and meters:** interpolate only when it helps compare values; announce exact values independently of motion.
- **Toasts and validation:** show concise text and semantic status; never rely on color or movement alone.

## Accessibility and performance

1. Reduced motion must be available from the operating system and the documented environment override.
2. Never autoplay decorative loops, parallax, repeated pulses, or flashing attention effects.
3. Preserve keyboard navigation, visible focus, screen-reader names, and text alternatives.
4. Prefer opacity and transforms (or the platform's equivalent) over repeated layout recalculation.
5. Keep animation work on the UI thread bounded; do not block input, file operations, scanning, compilation, or background tasks.
6. If a transition cannot maintain responsiveness, skip intermediate frames and render the latest state.
7. Status, errors, and completion are driven by real operation results, not animation timers.

## Implementation profile

Python / Tkinter desktop workbench

The platform adapter in this repository is deliberately small and opt-in. It centralizes timing, easing, and reduced-motion behavior without forcing a visual redesign. Add motion to a component only when the transition clarifies a state change or spatial relationship. Validate both normal and reduced-motion modes on the target operating systems.

## Review checklist

- [ ] The motion explains a real state or spatial relationship.
- [ ] Input is not delayed; transitions are interruptible.
- [ ] No text, control, chart, or focus indicator becomes unreadable mid-transition.
- [ ] Reduced motion removes nonessential movement without hiding information.
- [ ] Large lists and dashboards do not create stagger storms.
- [ ] The same action uses the same timing and easing across the application.
- [ ] Performance and keyboard operation remain intact.
