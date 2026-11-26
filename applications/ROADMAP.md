# Six Reaper applications — 20,000-line delivery plan

**Implementation language:** Reaper (.rpr).  
**Target:** 20,000 source lines for each application; 120,000 across the suite.  
**Current state:** foundation increment with domain functions, demonstration entry points and smoke scenarios.  
**Completion:** not claimed.

Each module allocation below is 2,000 source lines. Each application budget therefore totals exactly 20,000 lines.

## Omni

Unified DAK workspace, product registry, service health and explicit action routing.

| Module | Planned lines |
|---|---:|
| Registry and lifecycle | 2,000 |
| Workspace state and navigation | 2,000 |
| Service health and routing | 2,000 |
| Capabilities and permissions | 2,000 |
| Event orchestration | 2,000 |
| Resource monitoring | 2,000 |
| Recovery and snapshots | 2,000 |
| Localization and preferences | 2,000 |
| Audit and diagnostics | 2,000 |
| DOM and DAK host adapters | 2,000 |
| **Total** | **20,000** |

## Pomni

Local-first notes, tasks, reminders, calendar planning and personal knowledge.

| Module | Planned lines |
|---|---:|
| Notes and document model | 2,000 |
| Tasks and dependencies | 2,000 |
| Reminder policies | 2,000 |
| Calendar and planning | 2,000 |
| Knowledge graph and backlinks | 2,000 |
| Local search | 2,000 |
| Tags and collections | 2,000 |
| Offline sync and conflict handling | 2,000 |
| Import, export and backup | 2,000 |
| Localization and accessibility | 2,000 |
| **Total** | **20,000** |

## LoLo

Local communication, contact profiles, consent-aware drafts and bounded outbound queue.

| Module | Planned lines |
|---|---:|
| Contacts and local identities | 2,000 |
| Conversation and thread model | 2,000 |
| Composer and draft lifecycle | 2,000 |
| Bounded local outbox | 2,000 |
| Local sharing and handoff | 2,000 |
| Transport adapter contracts | 2,000 |
| Search and archive | 2,000 |
| Attachment metadata and limits | 2,000 |
| Privacy and consent policies | 2,000 |
| Localization and observability | 2,000 |
| **Total** | **20,000** |

## PePe

Metadata-first organization of files, collections and digital assets.

| Module | Planned lines |
|---|---:|
| Asset and metadata model | 2,000 |
| Collections and tags | 2,000 |
| Import and indexing contracts | 2,000 |
| Metadata extraction | 2,000 |
| Duplicate detection | 2,000 |
| Search and filters | 2,000 |
| Preview adapter contracts | 2,000 |
| Safe move and delete planning | 2,000 |
| Backup and export | 2,000 |
| Localization and audit history | 2,000 |
| **Total** | **20,000** |

## Hyper-kinetic Charge

Read-only telemetry interpretation and guarded power/performance recommendations.

| Module | Planned lines |
|---|---:|
| Telemetry contracts and sensor registry | 2,000 |
| Sensor validation | 2,000 |
| CPU and memory load models | 2,000 |
| Power profiles | 2,000 |
| Thermal guards | 2,000 |
| Battery planning | 2,000 |
| CPU/GPU recommendations | 2,000 |
| Scheduler hints | 2,000 |
| Benchmark history | 2,000 |
| Safety gates and regression coverage | 2,000 |
| **Total** | **20,000** |

## Judo

Permission review, trust policy, security posture reporting and remediation planning.

| Module | Planned lines |
|---|---:|
| Permission registry | 2,000 |
| Application trust and identity | 2,000 |
| Static configuration audit | 2,000 |
| Trust policy and provenance | 2,000 |
| Isolation profiles | 2,000 |
| Risk scoring | 2,000 |
| Incident timeline | 2,000 |
| Recovery checklists | 2,000 |
| Audit report and export | 2,000 |
| Localization and accessibility | 2,000 |
| **Total** | **20,000** |

## Common delivery gates

1. Reaper parser, type-checker and source-map validation for every .rpr file.
2. Positive, negative, boundary and property-oriented tests for domain and policy behavior.
3. Versioned DOM contracts for lifecycle, tasks, resources, messaging, reactive state, recovery and diagnostics.
4. Native DAK host adapters with least-privilege capability grants and deterministic failure behavior.
5. Native UI, EN/RU/UK localization, accessibility and reduced-motion behavior.
6. Resource limits, fault injection, offline recovery and security tests.
7. CI evidence on supported Intel/AMD x86-64 targets before maturity is raised.

Line count is a sizing target, not a quality metric by itself. New code must represent implemented behavior, tests, contracts or documented evidence. Generated filler and duplicated boilerplate do not count toward the target. Hardware controls, writes, deletion, networking and privilege changes remain unavailable until their adapters and approval paths exist.
