# Disney Motion System — Reaper Studio

Reaper Studio adopts a restrained, platform-native interpretation of the twelve animation principles. Motion communicates state and spatial continuity; it never delays editing, parsing, execution, debugging, or device inspection.

## Motion contract

- Preserve the existing Anatidae visual system and native Tk desktop architecture.
- Use short, deterministic, interruptible transitions; newer user actions supersede pending motion.
- Respect operating-system reduced-motion settings and `UI_REDUCED_MOTION=1`.
- Keep keyboard focus, status text, exact values, and diagnostic output available without animation.
- Never imply that a program, build, hardware action, or validation has completed before its real result exists.

## Shared timing tokens

| Token | Duration | Purpose |
|---|---:|---|
| instant | 0 ms | Reduced motion / immediate state |
| micro | 100 ms | Press and focus feedback |
| fast | 140 ms | Small control transition |
| standard | 180 ms | Menu and disclosure |
| spatial | 240 ms | Window or workspace transition |
| emphasis | 280 ms | Meaningful validation feedback |

## Twelve-principle mapping

1. Squash and stretch: restrained press feedback; never distort code, values, or diagnostics.
2. Anticipation: focus and hover preview actions without delaying activation.
3. Staging: keep one visual focus while preserving access to editor and output.
4. Straight-ahead / pose-to-pose: use explicit state transitions; continuous motion is reserved for continuous interactions.
5. Follow-through and overlap: bounded sequencing for related surfaces.
6. Slow in / slow out: consistent easing for entry, exit, and repositioning.
7. Arcs: optional for spatial navigation; dense workspaces remain direct.
8. Secondary action: status cues reinforce the real result.
9. Timing: use shared tokens; never block the Tk event loop.
10. Exaggeration: reserve emphasis for confirmed success or validation errors.
11. Solid drawing: preserve geometry, clipping, focus, and contrast.
12. Appeal: motion remains precise, restrained, and consistent with the workstation.

## Accessibility and performance

Reduced motion removes nonessential transitions but never hides information or changes the result. Avoid flashing, decorative loops, parallax, long stagger sequences, and per-row animation in large tables. Skip intermediate frames under load and render the latest state. Test keyboard operation and both motion modes on supported platforms.
