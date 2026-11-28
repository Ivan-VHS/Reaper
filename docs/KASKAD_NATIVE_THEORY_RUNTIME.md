## Purpose

Specify Reaper's native role in automated mathematical-theory improvement. Reaper is the sole source-level orchestration and semantic language for the pipeline. Pytyliki supplies bounded native corpus and exact-computation evidence.

This is an architecture contract. It does not claim that the current reference runtime, partial AOT compiler, or a production Kaskad integration already satisfies it.

## Reaper responsibilities

- Parse source documents into stable, source-mapped typed theory nodes.
- Model definitions, axioms, assumptions, claims, proof steps, counterexamples, dependencies, evidence, versions, and provenance.
- Validate signatures, domains/codomains, quantifiers, assumptions, proof references, and evidence/status transitions.
- Build and incrementally update the claim dependency DAG.
- Detect duplicate/near-duplicate claims, cycles, missing dependencies, unreferenced proof sections, stale documentation, and incompatible notation.
- Generate explicit proof obligations and bounded research tasks.
- Rank improvement candidates by mathematical impact, unresolved prerequisites, dependency centrality, verification cost, regression risk, and expected review value.
- Produce minimal source-mapped patch proposals, machine-readable reports, and a complete audit log.
- Dispatch exact and finite checks to the versioned Pytyliki evidence interface.

## Native execution requirement

The Kaskad pipeline must not invoke the Python reference runtime, Node/JavaScript, shell scripts, or any other external application-language runtime. The existing Python reference runtime may remain a temporary semantics oracle during migration, but is not an accepted production dependency.

The current AOT path also emits C17 and delegates compilation to a host C toolchain. That generated-C path is not compliant with this production boundary and must not be used by Kaskad jobs. The accepted target is Reaper-owned bytecode/VM execution or a direct native backend that does not generate or execute a third application language.

The current native AOT subset is not yet sufficient for the required data structures and workflow. Before activation, Reaper must provide native execution for the pipeline subset, including:

1. Typed records and versioned serialization for theory snapshots and evidence envelopes.
2. Deterministic lists/maps/sets and stable iteration order.
3. Bounded document and manifest input through explicit file capabilities.
4. Source spans and source-map preservation across parsing and transformations.
5. Module/import boundaries for theory modules and rule packs.
6. Exact integer and rational operations, checked overflow, and explicit approximation boundaries.
7. Deterministic graph/DAG algorithms with cycle witnesses and incremental invalidation.
8. Typed `Result`/error propagation with stable `RPR-E...` diagnostics.
9. Bounded execution, memory, recursion, input size, and output size.
10. Native conformance tests that compare the supported Reaper VM/bytecode/native paths.

Feature scope must be implemented in Reaper itself. A Python, JavaScript, shell, Rust, C++, or Java helper is not an acceptable substitute.

## Proposed typed module boundaries

These are module responsibilities, not assertions that the modules already exist:

- `theory.snapshot`: immutable snapshot identity and source manifest.
- `theory.source`: source nodes, spans, headings, and cross-references.
- `theory.claim`: claim kinds, stable IDs, scope, assumptions, and status.
- `theory.graph`: dependency DAG, incremental invalidation, and cycle witnesses.
- `theory.proof_obligation`: generated proof requirements and unresolved blockers.
- `theory.evidence`: exact/finite/empirical/numerical classifications and provenance.
- `theory.rules`: typed transformation rules with preconditions and preserved invariants.
- `theory.rank`: deterministic candidate ranking with explainable inputs.
- `theory.patch`: minimal source-mapped proposal generation, never a direct main write.
- `theory.audit`: append-only actions and decision records.
- `pytyliki.bridge`: explicit versioned native interface client.

## Candidate transformation protocol

Every proposed transformation must have:

- stable rule ID and rule-set version;
- typed input/output signatures;
- preconditions and explicit scope;
- preserved invariants;
- generated proof obligations;
- a counterexample/negative-case plan;
- expected changed paths and downstream invalidation;
- rollback information and deterministic output identity.

A candidate is rejected before patch generation when its preconditions fail, its scope is ambiguous, it changes a protected invariant, or it cannot preserve source provenance. A passing computational check is evidence only for the exact declared check.

## Scheduling and speed

- Build the DAG once per snapshot and update only the affected closure.
- Partition jobs by independent components and use stable ordering.
- Run cheap parse/type/contract checks before expensive exact or finite campaigns.
- Cache results by source hash, Reaper semantic version, rule-set version, Pytyliki interface version, and build identity.
- Support a fast per-commit lane and a full scheduled/on-demand research lane.
- Bound every job and preserve deterministic tie-breaking.
- Report actual cold/warm throughput, cache hits, graph size, task counts, resource use, and verification outcomes.

## Safety and scientific governance

- Read-only by default; no hidden network, shell, process, or arbitrary FFI effects.
- The bridge may invoke only the explicitly configured Pytyliki interface with a versioned capability.
- Generated changes are reviewable branch/PR proposals, never direct writes to protected main.
- No automatic theorem promotion, independent-review marking, or novelty declaration.
- Preserve K3 base notation and positional zero semantics unless a separate approved theory change says otherwise.
- Automated validation and human mathematical review are distinct evidence classes.

## Migration sequence

1. Close native-runtime feature gaps needed by the pipeline.
2. Establish Reaper-native differential conformance for the required subset.
3. Implement theory IR and graph/proof-obligation modules in `.rpr`.
4. Implement the Pytyliki bridge and evidence envelope.
5. Run end-to-end read-only Kaskad analysis.
6. Enable PR proposal generation behind an explicit maintainer-controlled switch.
7. Replace legacy CI entry points one at a time after parity proof.

## Acceptance

No production theory job may rely on Python or another external language runtime. The native path must pass deterministic, negative, boundary, differential, resource-limit, and source-map tests; the same snapshot must produce the same theory IR and audit manifest; and every generated change must remain reviewable and reversible.

## Status

Design contract only. Native runtime parity, modules, bridge, and Kaskad integration are not yet implemented.