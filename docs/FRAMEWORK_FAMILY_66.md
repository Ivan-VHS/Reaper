# Reaper Framework Family 66

## Purpose

The Reaper native core includes a catalogue and evidence-assessment API for 66
specialized repository-engineering frameworks. The names in the catalogue are
canonical Latin identifiers. Each framework has its own domain, specialization,
expected deliverable and minimum evidence set.

The family is grouped into eleven coordinated work areas:

| Area | Frameworks |
|---|---|
| Architecture | Jevron, Jarfen, Trexjon, Voljmer, Reijen, Drajen |
| Source quality | Spijron, Vexjor, Krejndar, Morjen, Tarjen, Flixjen |
| Security | Jorjan, Brejven, Keldjor, Vajpern, Grejmor, Teljorn |
| Delivery | Sajfern, Deljen, Roxjon, Meljorn, Kejron, Fenjer |
| Contracts and data | Vorjen, Trajven, Skorjen, Beljtor, Nexjen, Derjon |
| Verification | Kreijen, Veljkor, Tesjen, Morjden, Zefirn, Rexjen |
| Operations | Kajldor, Feljin, Vorjten, Trexjen, Seljven, Drajgon |
| Documentation | Kesjin, Brejden, Neljkor, Tevjin, Merjok, Jorven |
| Product experience | Rejnhar, Keljven, Fendjin, Vajden, Trevjorn, Skorjvin |
| Federation | Deljmor, Krejns, Veljin, Tesjendor, Morvajn, Zexjen |
| Governance | Rejnor, Kajlven, Fengjin, Vorjden, Trejns, Seljkorn |

## Individual framework specifications

| ID | Name | Domain | Specialization | Expected deliverable | Required evidence |
|---|---|---|---|---|---|
| jevron | Jevron | architecture | system topology discovery | versioned architecture graph and unresolved-boundary report | source, contracts, tests |
| jarfen | Jarfen | architecture | module and ownership boundaries | module ownership map and boundary violations | source, contracts, compatibility |
| trexjon | Trexjon | architecture | dependency graph and cycle analysis | deterministic dependency graph and cycle report | source, contracts, tests |
| voljmer | Voljmer | architecture | component decomposition and cohesion | component map with coupling and cohesion findings | source, contracts, tests |
| reijen | Reijen | architecture | requirement-to-implementation traceability | requirement coverage matrix with missing links | source, tests, documentation |
| drajen | Drajen | architecture | architecture decision and constraint analysis | decision record, assumptions and trade-off ledger | source, contracts, documentation |
| spijron | Spijron | source-quality | source inventory and ownership discovery | source inventory with module and language totals | source, tests, documentation |
| vexjor | Vexjor | source-quality | static source analysis and finding triage | prioritized static-analysis findings with source locations | source, tests, security |
| krejndar | Krejndar | source-quality | complexity and maintainability analysis | complexity baseline and bounded decomposition proposals | source, tests, performance |
| morjen | Morjen | source-quality | behavior-preserving refactor planning | refactor plan with compatibility checkpoints | source, contracts, tests, compatibility |
| tarjen | Tarjen | source-quality | public API and extension-point design | API surface inventory and compatibility contract | source, contracts, tests, documentation |
| flixjen | Flixjen | source-quality | coding convention and consistency audit | actionable consistency findings without automatic rewrites | source, tests, documentation |
| jorjan | Jorjan | security | threat modeling and attack-surface mapping | threat model with assets, trust boundaries and mitigations | source, contracts, security |
| brejven | Brejven | security | secret and credential exposure detection | redacted secret-pattern findings and remediation guidance | source, security |
| keldjor | Keldjor | security | privilege and capability-boundary review | least-privilege matrix and privilege escalation findings | source, contracts, tests, security |
| vajpern | Vajpern | security | dependency and software-supply-chain review | dependency provenance and supply-chain risk report | source, contracts, security |
| grejmor | Grejmor | security | vulnerability triage and secure-code review | severity-ranked security findings with evidence references | source, tests, security |
| teljorn | Teljorn | security | trust-boundary and untrusted-input analysis | input-boundary map with limits and rejection requirements | source, contracts, security, rollback |
| sajfern | Sajfern | delivery | build-system and toolchain integrity | build graph, toolchain constraints and reproducibility gaps | source, tests, compatibility |
| deljen | Deljen | delivery | test pipeline and test ownership design | test inventory and verification pipeline plan | source, tests |
| roxjon | Roxjon | delivery | continuous-integration workflow review | CI dependency graph and missing quality-gate report | source, tests, compatibility |
| meljorn | Meljorn | delivery | package and artifact construction | artifact manifest and packaging acceptance checklist | source, contracts, tests, rollback |
| kejron | Kejron | delivery | release staging and release readiness | release gate report with blocking evidence | tests, documentation, compatibility, rollback |
| fenjer | Fenjer | delivery | reproducible build and provenance analysis | reproducibility checklist and build-input provenance report | source, tests, compatibility |
| vorjen | Vorjen | contracts-data | schema definition and data-shape validation | versioned schema proposal and validation cases | contracts, tests, compatibility |
| trajven | Trajven | contracts-data | data and API migration planning | ordered migration plan with rollback checkpoints | contracts, tests, rollback |
| skorjen | Skorjen | contracts-data | serialization and interchange formats | serialization contract with round-trip and malformed-input cases | contracts, tests, compatibility |
| beljtor | Beljtor | contracts-data | persistence and data-integrity controls | integrity invariants and recovery verification plan | source, contracts, tests, rollback |
| nexjen | Nexjen | contracts-data | contract drift and schema compatibility | contract drift report and version-alignment actions | contracts, tests, compatibility |
| derjon | Derjon | contracts-data | backward and forward compatibility | compatibility matrix with explicit unsupported combinations | contracts, tests, compatibility |
| kreijen | Kreijen | verification | test strategy and acceptance-case design | test strategy covering normal, boundary and failure cases | source, tests |
| veljkor | Veljkor | verification | property, invariant and boundary testing | invariant catalogue and property-test plan | source, tests, security |
| tesjen | Tesjen | verification | regression detection and behavioral parity | regression matrix tied to changed behavior | source, tests, compatibility |
| morjden | Morjden | verification | module and service integration testing | integration scenarios with contract-level assertions | contracts, tests, compatibility |
| zefirn | Zefirn | verification | cross-repository contract verification | provider-consumer compatibility matrix and integration cases | contracts, tests, compatibility |
| rexjen | Rexjen | verification | performance baseline and benchmark validity | reproducible benchmark plan with workload and environment metadata | source, tests, performance |
| kajldor | Kajldor | operations | resource budgets and capacity limits | CPU, memory, storage and concurrency budget ledger | source, tests, performance |
| feljin | Feljin | operations | logging, diagnostics and observability quality | diagnostic coverage map with redaction and cardinality checks | source, security, documentation |
| vorjten | Vorjten | operations | health, readiness and lifecycle behavior | health/readiness contract and lifecycle transition tests | source, tests, rollback |
| trexjen | Trexjen | operations | fault containment and resilience testing | failure-mode matrix with bounded retry and timeout requirements | source, tests, rollback |
| seljven | Seljven | operations | rollback, recovery and safe restoration | recovery procedure and rollback verification matrix | source, tests, rollback |
| drajgon | Drajgon | operations | backup integrity and restore validation | backup inventory with integrity and restore test cases | source, tests, security, rollback |
| kesjin | Kesjin | documentation | documentation information architecture | documentation map with stale, orphaned and missing sections | source, documentation |
| brejden | Brejden | documentation | README and onboarding completeness | README audit with verified commands and implementation status | source, tests, documentation |
| neljkor | Neljkor | documentation | localization and terminology consistency | locale coverage matrix and terminology drift report | source, tests, documentation |
| tevjin | Tevjin | documentation | API and reference documentation | API reference gaps linked to actual public contracts | contracts, tests, documentation |
| merjok | Merjok | documentation | examples, tutorials and reproducible walkthroughs | example verification plan and missing learning paths | source, tests, documentation |
| jorven | Jorven | documentation | knowledge indexing and source traceability | local knowledge index with source and freshness references | source, contracts, documentation |
| rejnhar | Rejnhar | experience | accessibility and inclusive interaction audit | accessibility findings and keyboard/reduced-motion test plan | source, tests, documentation |
| keljven | Keljven | experience | UI and interaction contract consistency | UI state, input and error contract matrix | source, contracts, tests |
| fendjin | Fendjin | experience | localized interface behavior | UI locale coverage and fallback behavior report | source, tests, documentation |
| vajden | Vajden | experience | interaction performance and responsiveness | interaction latency budget and responsive-state test plan | source, tests, performance |
| trevjorn | Trevjorn | experience | end-to-end user workflow coherence | workflow map with state transitions and recovery paths | source, tests, documentation |
| skorjvin | Skorjvin | experience | product journey and end-to-end acceptance | user-journey acceptance matrix across integrated surfaces | source, tests, security, documentation |
| deljmor | Deljmor | federation | repository federation and ownership graph | cross-repository ownership and dependency map | source, contracts, compatibility |
| krejns | Krejns | federation | ABI, FFI and binary interoperability | ABI contract matrix with layout, calling-convention and error tests | contracts, tests, security, compatibility |
| veljin | Veljin | federation | platform and toolchain adaptation | platform capability matrix and fallback plan | source, tests, compatibility |
| tesjendor | Tesjendor | federation | plugin and extension lifecycle boundaries | extension contract with trust, version and lifecycle gates | source, contracts, security |
| morvajn | Morvajn | federation | shared-state synchronization and consistency | cross-repository consistency model and conflict plan | contracts, tests, compatibility, rollback |
| zexjen | Zexjen | federation | service and subsystem integration | integration boundary map with failure and timeout contracts | contracts, tests, security |
| rejnor | Rejnor | governance | evidence-based maturity and completeness | maturity assessment tied to executable exit criteria | contracts, tests, documentation |
| kajlven | Kajlven | governance | auditable evidence ledger and provenance | evidence ledger with claim, source, owner and verification state | source, tests, documentation |
| fengjin | Fengjin | governance | risk scoring and change control | risk register with impact, likelihood and mitigation evidence | source, tests, security |
| vorjden | Vorjden | governance | roadmap prioritization and dependency sequencing | prioritized roadmap with dependency and capacity assumptions | source, tests, documentation |
| trejns | Trejns | governance | change-impact analysis across components | change-impact graph and required regression scope | source, contracts, tests, compatibility |
| seljkorn | Seljkorn | governance | governed multi-framework orchestration | ordered execution plan with conflict, approval and rollback gates | source, contracts, tests, security, rollback |

## Native API

- `reaper_framework_catalog_count()` returns the fixed catalogue size (66).
- `reaper_framework_catalog_at(index)` returns a read-only profile.
- `reaper_framework_find(name_or_id)` resolves names and lowercase IDs
  case-insensitively.
- `reaper_framework_catalog_validate()` checks the registry's shape, Latin-only
  names, unique identifiers and evidence masks.
- `reaper_framework_assess(name_or_id, available_evidence)` calculates missing
  evidence against the profile's requirements.

Evidence flags cover source inventory, contracts, tests, security, performance,
documentation, compatibility and rollback. Framework-specific requirements are
stored with each profile and are exercised by native tests.

## CLI

List the family:

```sh
reaper-c --frameworks
```

Inspect one framework:

```sh
reaper-c --framework Jevron
```

The CLI emits catalogue information only. The assessment API accepts evidence
collected by its caller; it does not pretend to inspect a repository by itself.

## Safety and maturity

The initial implementation provides immutable framework profiles, lookup,
validation, evidence gates and native CLI discovery. It does not yet implement
66 independent source mutators or claim that every specialization has a
repository scanner. Framework assessment is fail-closed: missing evidence blocks
readiness, while complete evidence only produces `review-required`.

No framework can write repository files, install dependencies, access hardware,
transmit telemetry, approve its own changes, or merge a pull request. Any future
implementation adapter must have a bounded input contract, focused tests,
compatibility coverage and a human-controlled promotion path.
