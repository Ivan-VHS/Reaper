# Jora — Reaper-first application factory and unified store

**Projects:** Reaper / DAK  
**Contract:** \`reaper.jora.application.v1\`  
**Status:** first generator increment implemented; selected feature packs remain specification-only

## Product definition

Jora is the platform, application catalogue and generator. Every composed application is a separate product with its own independent name; application names must not contain `Jora`. A user chooses a product name, reusable capability packs, locale profiles and a preferred implementation target. The generator resolves dependencies, writes a versioned manifest with that application identity, and generates a Reaper project scaffold.

The composition formula is:

\`Application = Component 1 + Component 2 + ... + Component N + Dependencies + Locale Profile + Runtime Target\`

Example:

\`Text Editor + Audio Editor + Translator → Sonaris\`

A formula composes capability contracts; it does not concatenate arbitrary executable binaries. Each component declares a stable ID, version, provided interfaces, required interfaces, conflicts and maturity.

## Naming engine

Jora is the platform identity, never the generated application name. The naming engine derives independent product-name candidates from component domains and produces four name styles:

- compact: `Docs / Audio / Translate Workspace`;
- balanced: `Documents, Media & Languages Workspace`;
- descriptive: `Workspace for writing, audio editing & translation`;
- formula: `Text + Audio + Translation Workspace`.

The request may supply an explicit `name`; otherwise the selected `name_style` (`compact`, `balanced`, `descriptive` or `formula`) chooses a deterministic candidate. Every candidate and final application name is validated against the bound `application_name_policy`; any case or compatibility-normalized occurrence of `Jora` is rejected. The policy is carried by DAK in the request, revalidated by Reaper, and recorded in the generated manifest. Platform metadata, graph nodes and store labels may still identify Jora because they are not application product names. The manifest preserves the independent application name, platform metadata, semantic descriptors, selected label and all validated suggestions.

## Composition graph engine

A formula can produce several valid graphs from the same modules. Graph generation is deterministic for the same request and seed, and can emit 1–6 alternatives with a variation budget from 0–100. The user selects an optimization objective: balanced, low latency, modularity, extensibility or minimal complexity. Jora computes objective-specific scores alongside compatibility, capability reuse, planned-node count, longest synchronous path and structural complexity, then selects the highest-ranked candidate with stable tie-breaks.

Supported topologies:

| Topology | Structure |
|---|---|
| `layered` | interface → modules → required services |
| `pipeline` | modules connected in the selected workflow order |
| `hub_spoke` | shared application orchestrator routes work to modules |
| `plugin_mesh` | modules link when provided and consumed capabilities match |
| `event_driven` | modules publish/subscribe through an asynchronous event bus |
| `hybrid` | orchestrator plus compatible direct capability links |

Graph nodes carry identity, kind, label and maturity. Edges are typed (hosting, execution, mounts, requirements, workflow steps, capability links, events, extension registration and validation). Each graph has a canonical signature and metrics for nodes, edges, hard dependencies, capability connections, planned services and compatibility.

The engine keeps every synchronous control/data edge acyclic. Event feedback is permitted only through an explicit asynchronous event bus; it is excluded from startup ordering. A per-stage validator cannot release the next stage through a shared node that would introduce a synchronous cycle. The selected graph is the highest-scoring candidate, ranked by compatibility, reusable capability links, fewer planned nodes and then a stable signature tie-break. Optional extension registries and compatibility gates are marked `planned`, not falsely reported as implemented runtime services.

The complete graph set is embedded in `jora.app.json` and exported separately as `jora.graphs.json`. Every graph variant also has a `graphs/variant-*.mmd` Mermaid diagram. Each topology supports distinct direct, domain-grouped, capability-routed, stateful, validated and extensible rewrites. The lock file records graph signatures, the selected naming label, optimization objective and winning graph score for reproducible generation.

## Repository ownership

- **Reaper** owns request validation, the component catalogue, dependency resolution, product composition, deterministic naming, Reaper source scaffolding, localization bundle generation and the Jora CLI.
- **DAK** owns the desktop/store surface, package trust policy, approval flow and future native installation/update/rollback adapters.
- **Mora** is the DAK desktop surface. The Jora marketplace replaces the product identity of the former Mora Commons catalogue while preserving its existing desktop application ID.
- Generated applications are user-space projects. They do not become kernel modules.

## Composition pipeline

1. Capture selected capability packs, the Jora platform identity, an independent application name, and graph-generation preferences. The request binds `application_name_policy=no_platform_brand_in_application_name`.
2. Validate a versioned request, the immutable application-name policy, closed component IDs, unique selections and bounded collection sizes. Reaper independently rejects `Jora` in every application name, including case and compatibility-normalized variants.
3. Resolve dependency closure in deterministic dependency-first order; reject unknown edges and cycles.
4. Check component conflicts and incompatible options.
5. Choose Reaper as the canonical source generator. Other compiler targets are reported as pending until implemented and tested.
6. Generate a stable application ID from the canonical formula and graph settings. The selected application name remains independent of the Jora platform; the name and graph settings form a stable application ID.
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
6. Connect the store to a DAK native package manager only after signature verification, process isolation, capability enforcement and rollback are implemented.


## Expanded capability registry and bounded composition

The first-party catalogue now contains 21 canonical capability packs across document editing, audio, translation, subtitles, notes, task boards, calendars, speech, code, spreadsheets, image/video, presentations, files, APIs, automation, analytics, databases, archives and knowledge graphs. These are versioned specification contracts, not claims that all corresponding application engines are executable.

For formulas above 12 components, every graph variant adds domain cluster gateways and routes component membership through those gateways. Capability providers are indexed once and each consumed capability resolves to at most four deterministic local providers. This avoids all-pairs capability scans and bounds the direct integration neighbourhood. Per-generation limits are finite: 24 components, 128 graph nodes, 512 edges, six variants and the existing request/output byte limits.

When `language_targets` is `auto`, Reaper remains the generated core. Additional targets are selected from declared component preferences (Python for text/data/content work, Rust for systems/media work, TypeScript for selected visual interfaces). Toolchain presence is reported separately; all additional targets stay `adapter_pending` until a tested generator backend exists. Selection does not imply that an auxiliary source module has been generated.
