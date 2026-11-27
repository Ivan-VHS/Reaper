# Semantic Hypergraph and Source-Document Implementation Map — Reaper

**Feature:** Semantic Lake Graph (SLG)

**Scope:** a typed, content-addressed dataflow graph beside the existing Reaper text, AST, stack IR, Python reference runtime and native C17 toolchain.

The uploaded Constitution of the DAKs / AETHER-ANAS manifesto is the architectural source. This document traces its ten renunciations, twelve commandments, 66 engineering laws, twelve formula models and engineering rule catalogue into this repository. It separates shipped behavior from roadmap.

## 1. Why a sidecar graph

Reaper uses human-reviewable .rpr text, source locations, a Python parser/runtime and a developing native parser/IR. Removing text files before graph serialization, migration, reproducible export, semantic merge and review tooling exist would weaken auditability. Semantic Lake Graph adds a typed graph representation without replacing the source language.

The graph uses SHA-256 over canonical semantic JSON as its content address. Human labels are excluded from the digest. Edges connect a source output type to one target input port. Schema v1 is acyclic; feedback requires an explicit delay/state node in a later schema.

## 2. Implemented contract

Module: reaper/semantic_graph.py. Tests: tests/test_semantic_graph.py.

- Nodes carry operation, ordered input types, output type, declared effects and an optional finite JSON scalar literal.
- Semantic identity is SHA-256 over canonical sorted JSON; label changes do not change identity.
- Typed edges are checked against the exact target port.
- An input port can be connected only once.
- Duplicate IDs, forged hashes, dangling references, invalid ports, type mismatch and cycles are rejected.
- Optional completeness checking verifies that every input port is connected.
- to_dict() emits a deterministic, sorted, versioned JSON projection.

This module does not execute graphs, schedule CPU/GPU/remote workers, prove arbitrary program termination, infer full dependent types or persist a binary graph database. It is a typed graph substrate and validation API.

## 3. Ten renunciations mapped to Reaper

| Source doctrine | Repository realization | Status / guardrail |
|---|---|---|
| Three-medium existence | Graph is medium-independent; existing flow operator, runtime/VM and platform abstractions remain execution foundations. | Unified CPU/GPU/remote executor is roadmap. |
| Hydrodynamic calm | Readable .rpr, flow-first pipelines, deterministic projection, friendly diagnostics and source spans. | Partial and incremental. |
| Ontological dak typing | Structural graph-port types plus current AST/IR verification and feature contracts. | Partial; not a complete static type checker. |
| Feather-oil / effects | Runtime limits, governance/consent adapters and effect-aware contracts. | Partial; not a complete algebraic-effects runtime. |
| Flock concurrency | Graph can inform dataflow scheduling. | Scheduler, bounded worker queues and backpressure remain executor work. |
| Rounded visual design | Reaper Studio follows shared Anatidae UI, motion and accessibility contracts. | Design contract. |
| Hypergraph instead of text | Semantic Lake Graph is an additional typed graph representation. | Implemented prototype; text/AST/IR remain canonical authoring path. |
| Names as identity | Node SHA-256 address; label rename preserves identity. | Implemented for graph nodes only. |
| Habitats / FBIP | Runtime resource accounting and native backend provide groundwork. | Partial; Python allocator is not a region/FBIP guarantee. |
| Immune inputs / transparent cost | Quotas, audit, bounded parser/runtime input and feature status. | Partial; full taint/refinement/resource types remain roadmap. |

## 4. Twelve Creator commandments — acceptance crosswalk

1. **Uniqueness:** graph storage is an independent representation, not a second grammar.
2. **Zero ambiguity:** semantic nodes and typed edges have one validated interpretation.
3. **Orthogonality:** operations, types, effects, labels and edges are independent.
4. **Human-centrism:** diagnostics identify the offending node, port, type or cycle.
5. **Instant feedback:** incremental validation is to be measured; 16 ms is a test target, not a universal guarantee.
6. **Self-hosting:** Python remains the reference runtime; native C17 is not yet a full self-hosted compiler.
7. **Seamless bridge:** FFI remains opt-in; a graph node cannot silently invoke external effects.
8. **Cognitive scaling:** surface syntax stays beginner-friendly while graph/type/effect concepts appear progressively.
9. **Computational ecology:** canonicalization and graph checks are bounded by input size.
10. **Stable core:** schema version reaper.semantic-graph/v1 and explicit migrations.
11. **Open tooling:** deterministic projections are exposed for tools and validators.
12. **Creative joy:** legibility and actionable feedback outrank clever opaque syntax.

## 5. Sixty-six engineering laws

The original numbered laws are preserved as six review families:

- **1–14, physics/state:** account for costs, constrain hidden state, explicit unsafe boundaries, deterministic resource release, low coupling, immutable defaults and no hidden cross-module mutation. Reaper anchors: runtime quotas, resource tracking, audit and module boundaries.
- **15–26, mechanics/flow:** composable flow, bounded queues, explicit FFI, deterministic platform contracts and readable control flow. Anchors: flow operator, runtime/VM, QCS and C17 bridge.
- **27–40, types/logic:** decidable verification, bounded compile-time work, ADTs, exhaustive matching, explicit numeric conversion, unambiguous overloads, complexity contracts and stable IR. Anchors: Python/C IR, optimizer and feature contracts.
- **41–50, evolution/biology:** versioned feature incubation, fault isolation, deprecation, incremental IDE integration, taint boundaries and cognitive load. Anchors: language/features.json, validator, editor and governance docs.
- **51–64, systems:** concurrency, data-parallel scaling, explicit network failures, independent modules, canonical formatting, cache locality, introspection, POLA, CQS, bounded evaluation and bootstrapping. Anchors: runtime, VM, native toolchain, federation, platform docs and CI.
- **65–66, readability/proof:** optimize for readability/debuggability and measure strength by defects rejected before execution.

## 6. Twelve special law/formula models

Trauman, Baus–Bayes, Gause, Strauss, Bergmann, Dilman, Tilman, Spillman, Besse, Hess, Messe and Little–Tillman–Yoshia are treated as engineering analogies: runtime overhead, resilient inference, semantic non-duplication, feature evolution, API surface, error growth, bottleneck optimization, diminishing returns, library granularity, deterministic rewrites, dependency isolation and queue saturation. They inform design trade-offs; they are not asserted as unverified physical laws governing a compiler.

## 7. Six hundred sixty-six source rules — range mapping

| Source range | Primary theme | Reaper realization |
|---|---|---|
| 1–111 | Three-medium existence / computation ontology | Flow-first language, canonical IR, platform profiles and the Semantic Lake Graph identity/edge layer; cross-device execution remains staged. |
| 112–222 | Hydrodynamic calm / transparency | .rpr syntax, source spans, friendly diagnostics, deterministic graph projection, runtime audit and tool feedback. |
| 223–333 | DAK typing / type system | IR type validation, typed graph ports, explicit effects and feature registry; full ADT/refinement checking remains roadmap. |
| 334–444 | Feather-oil / effects / immune barrier | Runtime quotas, resource tracking, governance, consent, FFI boundaries and validated inputs; full affine/effect typing is not claimed. |
| 445–555 | Flock / collective concurrency | Flow graph representation; worker scheduling, bounded concurrent execution and backpressure remain executor work. |
| 556–666 | Anti-angularity / freedom / creator | Multilingual aliases, editor configuration, readable docs, deterministic interchange and versioned schemas. License remains Apache-2.0; no automatic CC0 change. |

The engineering constitution is a specification corpus, not a count of implemented functions. Status remains explicit: planned, specified, implemented, verified or deprecated.

## 8. Type-system and maxim-compendium crosswalk

The source's strong/weak typing discussion maps to AST/IR contracts, explicit numeric operations, unambiguous conversions and graph-port compatibility. The maxim compendium's epistemology, systems, strategy, social and prevention themes become review heuristics: verify evidence, avoid local-optimum tuning, contain cascades, keep feedback actionable, distribute responsibility and prevent defects at boundaries. Heuristics never override tests or source evidence.

## 9. Tri-Color DAK UI

Use the shared 65/25/10 palette: porcelain white (#FFFFFF / #F4F7FB), cobalt/azure (#0052CC / #0A1F44) and signal red (#E62E2D / #FF4D4F). Maintain contrast, keyboard navigation, visible focus, localization and reduced-motion support. Motion never replaces a textual status.

## 10. Acceptance criteria

- Label-only rename preserves content_id; semantic change changes the content address.
- Wrong-type edges, duplicate target-port connections, dangling edges, forged IDs and cycles fail validation.
- JSON projection remains stable and versioned.
- Text/AST/IR workflows continue without graph features enabled.
- Native/Python parity claims remain evidence-based; a graph prototype does not make the native compiler complete.

## 11. Implementation anchors

New: reaper/semantic_graph.py and tests/test_semantic_graph.py.

Existing: reaper/ir.py, src/ir.c, include/reaper/ir.h, src/optimizer.c, language/features.json, tools/validate_features.py, docs/ANATIDAE_CONSTITUTION.md, docs/ENGINEERING_CONSTITUTION_PROFILE.md, docs/MOST_FUNCTION_CONTRACT_REGISTRY.md, docs/MOST_IMPLEMENTATION_STATUS.md and docs/REAPER_UNIFIED_ARCHITECTURE.md.
