# Reaper Skeleton Frameworks — design

## Intent

Implement the first five of the requested 330 frameworks for Reaper's systems-programming profile. The frameworks provide independent, pure validation contracts for assembling project and component skeletons.

## Goals

- Ship five separately importable Reaper-language modules.
- Keep each module responsible for one distinct boundary: project inventory, layer ordering, lifecycle transitions, capabilities, or extension compatibility.
- Define bounded, deterministic inputs and explicit outputs.
- Verify behavior using the existing Reaper interpreter and repository test harness.
- Include Reaper source modules in built distributions.

## Non-goals

- No general process supervisor, scheduler, plugin loader, privilege broker or package installer.
- No filesystem, network, subprocess, native-FFI or hardware effects.
- No claim that remaining 325 framework slots are implemented.

## Constraints

- Preserve current .rpr syntax and module loader.
- Keep Python as the repository's current compatibility runtime; the framework logic itself is written in Reaper.
- Do not modify main directly; use a feature branch and reviewable pull request.
- Keep all APIs independent, with no shared mutable state or implicit cross-module imports.

## Approaches considered

1. One generic framework engine with five descriptors: smallest code surface, but it would collapse distinct responsibilities into metadata and duplicate the repository's existing catalogue pattern.
2. Five Reaper modules with separate contracts: more explicit APIs and independently testable behavior; selected.
3. Five native C17 libraries: unsuitable for this first batch because native language/compiler parity remains partial and the requested frameworks should be authored in Reaper.

## Selected framework contracts

- FrameManifest: report missing required components and reject duplicate/empty names.
- FrameLayers: validate ordered layer edges; only forward edges are legal, making cycles impossible by construction.
- FrameLifecycle: accept only declared state transitions and reject malformed/duplicate transition tables.
- FrameCapabilities: require every requested capability to be granted and every grant to be allowed by policy.
- FrameExtensions: validate unique extension IDs and inclusive host API compatibility intervals.

## Acceptance

Each framework has positive and negative Reaper-interpreter tests, a documented module API, and package-data integration. The batch remains in review until the exact pull-request head has a successful CI run.
