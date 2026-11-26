# Reaper 325 Frameworks — design

## Intent

Complete the 65 remaining domains (numbers 02–66) with five independently importable Reaper-language framework modules per domain. Together with batch 01, the programme contains 66 domains × 5 frameworks = 330 modules.

## Selected implementation shape

Each framework is a standalone `.rpr` module in `reaper/frameworks/<domain>/`. The first completion wave standardizes five foundational contracts per domain: a strict registry, a capacity admission check, a dependency graph validator, a missing-requirement resolver and a lifecycle transition validator. API names are domain-scoped; modules do not import one another and contain no shared mutable state.

This shared contract family is an intentional common baseline, not a claim that all 325 modules provide domain-specific schedulers, loaders, drivers or native execution. Such privileged/runtime capabilities remain separate work and require their own platform-specific contracts.

## Goals

- Provide 325 distinct import paths and API names, with no catalogue-only entries.
- Implement all framework behavior in Reaper source.
- Exercise each module through the existing interpreter with positive and negative fixtures.
- Keep all algorithms deterministic, bounded by interpreter quotas and free of ambient host effects.
- Include all modules in installed package data and in CTest/CI.
- Track each domain and module by stable ID, source path and acceptance evidence.

## Non-goals

- No implicit filesystem, network, subprocess, native FFI, driver installation, physical MMIO or flashing.
- No claim that the reference interpreter is a security sandbox.
- No automatic merge or change to `main` before CI and review.

## Acceptance

The index must contain exactly 65 domains and 325 unique modules. Every module must exist, import, pass a valid fixture and produce the specified result for a negative fixture. Full repository tests, packaging checks and CI on the exact PR head are required before the batch is marked delivered.
