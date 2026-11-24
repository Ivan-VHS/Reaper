# Jora — Reaper-first application factory and unified store

**Projects:** Reaper / DuckOS  
**Contract:** \`reaper.jora.application.v1\`  
**Status:** first generator increment implemented; selected feature packs remain specification-only

## Product definition

Jora unifies an application marketplace with a compositional application factory. A user chooses reusable capability packs, locale profiles and a preferred implementation target. Jora resolves their dependencies, derives a product identity, writes a versioned manifest and generates a Reaper project scaffold.

The composition formula is:

\`Application = Component 1 + Component 2 + ... + Component N + Dependencies + Locale Profile + Runtime Target\`

Example:

\`Text Editor + Audio Editor + Translator = LexiTone 3D\`

A formula composes capability contracts; it does not concatenate arbitrary executable binaries. Each component declares a stable ID, version, provided interfaces, required interfaces, conflicts and maturity.

## Repository ownership

- **Reaper** owns request validation, the component catalogue, dependency resolution, product composition, deterministic naming, Reaper source scaffolding, localization bundle generation and the Jora CLI.
- **DuckOS** owns the desktop/store surface, package trust policy, approval flow and future native installation/update/rollback adapters.
- **Mora** is the DuckOS desktop surface. The Jora marketplace replaces the product identity of the former Mora Commons catalogue while preserving its existing desktop application ID.
- Generated applications are user-space projects. They do not become kernel modules.

## Composition pipeline

1. Capture a selection of capability packs, optional product name, UI locales and preferred locale.
2. Validate a versioned request, closed component IDs, unique selections and bounded collection sizes.
3. Resolve dependency closure in deterministic dependency-first order; reject unknown edges and cycles.
4. Check component conflicts and incompatible options.
5. Choose Reaper as the canonical source generator. Other compiler targets are reported as pending until implemented and tested.
6. Generate a stable application ID from canonical composition inputs and derive a readable product name from the selected formula.
7. Write a project manifest, lock file, localized interface dictionaries, Reaper entry point and component contract stubs.
8. Build into a sibling staging directory, then atomically rename it into a previously unused destination.
9. Validate generated files and run a Reaper static check in the host integration before any future package can be promoted.
10. Publish only after implementation, tests, permissions, dependency/license inventory, provenance and rollback gates pass.

## Languages and locales are separate dimensions

- **Implementation language:** Reaper \`.rpr\` is the only current Jora source generator. The first generated source profile is Reaper \`flow\`.
- **UI locales:** EN, RU, UK and MOST can be selected independently and are emitted as JSON dictionaries. MOST is a Russian-language Reaper profile, not a separate natural language.
- **Additional compiler targets:** Java, Kotlin, Python, TypeScript, Rust and C may appear in a request. They remain \`adapter_pending\` until a backend, tests and parity fixtures exist.

The existing Reaper language matrix is a toolchain/capability inventory, not proof that these languages can already be emitted as source.

## First-party component catalogue

| Component | Capability intent | Maturity |
|---|---|---|
| \`text.editor\` | document editing, search, formatting and history | specification only |
| \`audio.editor\` | audio assets, timeline and editing operations | specification only |
| \`translation.workspace\` | translation, terminology and review | specification only |

Supporting contracts include document and media models, a timeline model, local storage, localization and a translation provider. Locale files are generated. Storage, translation services, and audio-engine behavior are not silently supplied by the scaffold.

## Generated project layout

\`\`\`text
<application>/
  README.md
  jora.app.json
  jora.lock.json
  src/
    main.rpr
    components/
      text_editor.rpr
      audio_editor.rpr
      translation_workspace.rpr
  locales/
    en.json
    ru.json
    uk.json
    most.json
\`\`\`

The \`.rpr\` entry point and component files are valid scaffolding records, not implementations of a text editor, audio editor or machine-translation engine. The manifest explicitly reports \`installable=false\`, \`executable_capabilities=[]\`, and \`maturity=scaffold_only\`.

## Commands

\`\`\`sh
reaper jora catalog --json
reaper jora compose --request ./jora-request.json --json
reaper jora build --request ./jora-request.json --output ./LexiTone --json
\`\`\`

Example request: \`examples/jora/text-audio-translation.request.json\`.

## Store release gates

A component may be marked implemented only when it includes:

- an immutable component ID and semantic version;
- a versioned input/output contract and dependency constraints;
- implementation for the declared runtime;
- unit, integration, compatibility and resource-limit tests;
- explicit filesystem, network, audio and device permissions;
- dependency and licence inventory;
- reproducible build evidence and content hashes;
- signed provenance and rollback-compatible package metadata.

A catalogue entry, scaffold generation or successful JSON validation is not evidence of executable functionality.

## Security and failure model

- Requests and component lists are bounded. Unknown fields and IDs are rejected.
- Dependencies resolve only from a closed first-party catalogue.
- Build paths must not be symlinks; existing output paths are never overwritten.
- Files are prepared in a staging directory before atomic publication.
- Jora never runs generated source, invokes shell commands, installs packages, elevates privileges or grants device/network access.
- Translation, storage and audio services require future explicit host adapters and user grants.

## Next implementation increments

1. Move catalogue metadata into signed, schema-validated component packages.
2. Generate shared interface contracts and conformance fixtures for each pack.
3. Implement document models and local project storage.
4. Deliver actual text editing, audio editing and translation modules.
5. Add Java/Kotlin/TypeScript/native emitters with differential tests before advertising them as generated targets.
6. Connect the store to a DuckOS native package manager only after signature verification, process isolation, capability enforcement and rollback are implemented.
