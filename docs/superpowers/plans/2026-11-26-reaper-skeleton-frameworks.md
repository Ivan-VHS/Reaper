# Reaper Skeleton Frameworks — implementation plan

**Spec:** [Skeleton Frameworks design](../specs/2026-11-26-reaper-skeleton-frameworks-design.md)

## Global constraints

- Implement behavior in Reaper `.rpr` modules.
- Use only existing parser/runtime syntax and built-ins.
- No hidden host effects, network, native loading or hardware access.
- Tests exercise modules through `Interpreter.run`; test code is only the existing host test harness.
- Keep all five modules independent and export stable, narrow contracts.

## Task 1 — FrameManifest

Create `reaper/frameworks/skeleton/manifest.rpr` with `missing_components` and `valid_manifest`. Test complete, missing, duplicate, empty and malformed names. Expected: deterministic missing list and boolean acceptance.

## Task 2 — FrameLayers

Create `layers.rpr` with `valid_layer_graph`. Edges are two-element numeric pairs and must go strictly from lower to higher layer index. Test valid fan-out/fan-in and reject backward, self, out-of-range, malformed and duplicate edges.

## Task 3 — FrameLifecycle

Create `lifecycle.rpr` with `valid_lifecycle`. Validate the transition table before replaying the requested state sequence. Test valid sequence, undeclared transition, malformed pair and duplicate pair.

## Task 4 — FrameCapabilities

Create `capabilities.rpr` with missing/unexpected reports and `valid_capability_boundary`. Required capabilities must be granted; all grants must be in policy. Test missing requirements, over-grants and duplicate/malformed names.

## Task 5 — FrameExtensions

Create `extensions.rpr` with record validation, registry validation and host-compatible filtering. Test malformed record, duplicate ID, inverted interval and inclusive lower/upper bounds.

## Task 6 — Packaging and documentation

Add framework packages, include the Reaper modules in setuptools package data, document module contracts and link the batch tracker from the documentation index.

## Task 7 — Verification

Run `python -m unittest tests.test_skeleton_frameworks -v`, then the complete reference-runtime suite and required CMake/CTest path. Confirm the CI result for the exact PR head. Do not mark the batch delivered until these checks pass.
