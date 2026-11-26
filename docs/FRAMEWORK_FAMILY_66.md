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
