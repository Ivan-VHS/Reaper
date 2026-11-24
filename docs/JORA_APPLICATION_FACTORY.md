# Jora — Reaper-first application factory and unified store

**Projects:** Reaper / DuckOS  
**Contract:** \`reaper.jora.application.v1\`  
**Status:** first generator increment implemented; selected feature packs remain specification-only

## Product definition

Jora is one unified product: its catalogue, composer, generator and every composed application all carry the single name **Jora**. A user chooses reusable capability packs, locale profiles and a preferred implementation target. Jora resolves dependencies, writes a versioned manifest with the fixed product name Jora, and generates a Reaper project scaffold.

The composition formula is:

\`Application = Component 1 + Component 2 + ... + Component N + Dependencies + Locale Profile + Runtime Target\`

Example:

\`Text Editor + Audio Editor + Translator = Jora\`

A formula composes capability contracts; it does not concatenate arbitrary executable binaries. Each component declares a stable ID, version, provided interfaces, required interfaces, conflicts and maturity.

## Naming engine

The canonical product name is always **Jora**. The naming engine does not create unrelated brands for combinations. Instead, it derives human-readable descriptors from component domains and produces four presentation variants under the Jora identity:

- compact: `Jora · Documents · Audio · Languages`;
- balanced: `Jora — Documents & Audio & Languages Workspace`;
- descriptive: `Jora | Workspace for Documents & Audio & Languages`;
- formula: `Jora — Documents + Audio + Languages`.

The request selects `name_style` (`compact`, `balanced`, `descriptive` or `formula`). The manifest preserves `name = "Jora"`, the semantic descriptors, selected label and all suggestions. Labels are generated from the capability taxonomy rather than arbitrary syllable concatenation, and remain presentation metadata rather than independent application names.

## Composition graph engine

A formula can produce several valid graphs from the same modules. Graph generation is deterministic for the same request and seed, and can emit 1–6 alternatives with a variation budget from 0–100. The user selects an optimization objective: balanced, low latency, modularity, extensibility or minimal complexity. Jora computes objective-specific scores alongside compatibility, capability reuse, planned-node count, longest synchronous path and structural complexity, then selects the highest-ranked candidate with stable tie-breaks.

Supported topologies:

| Topology | Structure |
|---|---|
| `layered` | interface → modules → required services |
| `pipeline` | modules connected in the selected workflow order |
| `hub_spoke` | shared Jora orchestrator routes work to modules |
| `plugin_mesh` | modules link when provided and consumed capabilities match |
| `event_driven` | modules publish/subscribe through an asynchronous event bus |
| `hybrid` | orchestrator plus compatible direct capability links |

Graph nodes carry identity, kind, label and maturity. Edges are typed (hosting, execution, mounts, requirements, workflow steps, capability links, events, extension registration and validation). Each graph has a canonical signature and metrics for nodes, edges, hard dependencies, capability connections, planned services and compatibility.

The engine keeps every synchronous control/data edge acyclic. Event feedback is permitted only through an explicit asynchronous event bus; it is excluded from startup ordering. A per-stage validator cannot release the next stage through a shared node that would introduce a synchronous cycle. The selected graph is the highest-scoring candidate, ranked by compatibility, reusable capability links, fewer planned nodes and then a stable signature tie-break. Optional extension registries and compatibility gates are marked `planned`, not falsely reported as implemented runtime services.

The complete graph set is embedded in `jora.app.json` and exported separately as `jora.graphs.json`. Every graph variant also has a `graphs/variant-*.mmd` Mermaid diagram. Each topology supports distinct direct, domain-grouped, capability-routed, stateful, validated and extensible rewrites. The lock file records graph signatures, the selected naming label, optimization objective and winning graph score for reproducible generation.

## Repository ownership

- **Reaper** owns request validation, the component catalogue, dependency resolution, product composition, deterministic naming, Reaper source scaffolding, localization bundle generation and the Jora CLI.
- **DuckOS** owns the desktop/store surface, package trust policy, approval flow and future native installation/update/rollback adapters.
- **Mora** is the DuckOS desktop surface. The Jora marketplace replaces the product identity of the former Mora Commons catalogue while preserving its existing desktop application ID.
- Generated applications are user-space projects. They do not become kernel modules.

## Composition pipeline

1. Capture selected capability packs, the fixed Jora identity, naming style, UI locales and graph-generation preferences.
2. Validate a versioned request, closed component IDs, unique selections and bounded collection sizes.
3. Resolve dependency closure in deterministic dependency-first order; reject unknown edges and cycles.
4. Check component conflicts and incompatible options.
5. Choose Reaper as the canonical source generator. Other compiler targets are reported as pending until implemented and tested.
6. Generate a stable application ID from the canonical formula and graph settings. Jora remains the only product name; generated naming variants are descriptive labels such as `Jora — Documents & Languages Workspace`, never separately branded products.
7. Write a project manifest, lock file, localized interface dictionaries, Reaper entry point, component contracts and a separate graph-set artifact.
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
reaper jora build --request ./jora-request.json --output ./Jora --json
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
