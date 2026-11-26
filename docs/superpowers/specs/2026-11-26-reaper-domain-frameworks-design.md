# Reaper Domain Frameworks — batches 02–05

## Intent

Extend the first Reaper skeleton batch with genuinely domain-specific implementations for Platform, Environment, Infrastructure and Architecture. These are four distinct domains, not a repeated catalogue of generic validators.

## Implementation choices

Each framework is a standalone `.rpr` module with a stable, domain-scoped exported API. Platform modules deal with machine targets, ABI, instruction features, cross-build toolchains and memory maps. Environment modules resolve layered settings, validate environment variables and paths, enforce profile uniqueness and apply locale fallback. Infrastructure modules reason about service dependencies, residual resource capacity, readiness quorum, failure-domain diversity and aggregate health. Architecture modules validate layer order, compute transitive change impact, profile coupling matrices, enforce module boundaries and compare versioned contracts.

The existing Reaper reference interpreter remains the execution engine for this batch. The implementation avoids introducing a second Python implementation of the framework logic.

## Safety

These modules are pure, deterministic validators and planners. They do not read host environment variables, access files, start processes, load native libraries, map physical memory or perform network operations. Memory maps are metadata only.

## Acceptance

Every module must import independently and pass one valid and one invalid interpreter fixture. The programme index tracks 330 total slots, including the five original modules, and records pending source slots separately from delivered code.
