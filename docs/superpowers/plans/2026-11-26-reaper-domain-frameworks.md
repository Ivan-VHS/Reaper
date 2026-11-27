# Reaper Domain Frameworks — implementation plan for batches 02–05

**Spec:** [Domain Frameworks design](../specs/2026-11-26-reaper-domain-frameworks-design.md)

1. Add interpreter-driven tests and fixtures for 20 domain-specific contracts before production modules.
2. Implement five Platform modules: target profile, ABI contract, feature gate, cross-build plan and memory map.
3. Implement five Environment modules: manifest, config overlay, workspace root guard, profile chain and locale fallback.
4. Implement five Infrastructure modules: service DAG, resource allocator, readiness quorum, failure-domain placement and health reducer.
5. Implement five Architecture modules: layer graph, impact cone, coupling matrix, module boundary and semantic-version compatibility.
6. Add 4 package roots, setuptools package discovery, package data, CTest registration and CI step.
7. Add module/API documentation and update the 330-slot tracker with explicit pending counts.
8. Run focused tests, complete unittest discovery, package build, CMake build and CTest; inspect exact PR-head Actions results.

Do not mark the remaining 305 slots delivered or imply that metadata-only hardware/privilege interfaces execute.
