# Federated Reaper migration strategy

**Status date:** 2026-11-21  
**Principle:** Reaper becomes the shared language and execution platform only as each capability reaches tested native parity. A repository is not migrated merely because a parser library or a `.rpr` file was copied into it.

## Reaper self-hosting sequence

| Stage | Deliverable | Exit condition |
|---|---|---|
| 0 | Reaper-written lexer | token-by-token parity with the reference lexer, including Unicode identifiers, aliases, escapes and source locations |
| 1 | Reaper-written parser | full declarations, functions, blocks, control flow, calls, lists and indexing; canonical AST parity |
| 2 | Semantic analysis and evaluator | differential result/error parity with the reference interpreter |
| 3 | Canonical IR and verifier | deterministic IR and rejection of malformed or unsafe IR |
| 4 | Optimizer | semantics-preserving passes, bounded work and reproducible output |
| 5 | Native compiler and toolchain | generated code passes the same conformance corpus |
| 6 | Bootstrap closure | the compiler rebuilds its own sources reproducibly from a clean bootstrap |

Python remains a compatibility oracle and test orchestrator until these gates pass. The C17 native path is a bootstrap substrate, not yet a full replacement.

## Repository adoption matrix

| Repository | Existing foundation | Reaper adoption now | Migration boundary |
|---|---|---|---|
| **Reaper** | Python reference runtime, Reaper-written lexer and partial parser, C17 native lexer/expression parser | Continue implementing lexer/parser and canonical AST in `.rpr`; differential tests against Python and C | Do not remove Python, or claim self-hosting, before full runtime and bootstrap parity |
| **Pytyliki** | Native C11 processor/DSP core and stable C ABI | First integration: vendor Reaper's native lexer and single-expression parser as a separate C11 library; dedicated CLI and tests | Does not execute complete `.rpr` programs; no changes to processor/DSP core or ABI v1 |
| **OPlague** | Python Windows device/driver inspection, read-only reports and OS integration | Later candidate: move pure, deterministic policy/normalization/manifest validation only after Reaper has a stable evaluator and native host boundary | Keep Windows inventory and package inspection behind explicit OS adapters; do not replace Windows APIs with a language runtime |
| **VentuSample** | Native C++20 renderer, DSP, plugin manager and Qt desktop app | Later candidate: optional project/preset metadata and offline orchestration once the evaluator and deterministic interop contract are stable | Keep audio rendering, DSP kernels, timing-sensitive work and the C++20 plugin host native; never run interpreter work in an audio callback |

## Shared integration rules

1. Reaper source owns portable language-level policy and orchestration; host-specific OS, audio, device, filesystem and process operations remain explicit adapters.
2. Native dependencies are pinned to an upstream commit and preserve the upstream license.
3. Imported libraries remain isolated targets with narrow APIs. They do not grant filesystem, network, shell, process, driver, hardware or realtime permissions.
4. Each recipient keeps its native core and public ABI stable unless a separately reviewed change proves compatibility.
5. An integration is marked `implemented` only after clean-build CI, tests on supported platforms and explicit acceptance evidence. Parser-only integrations remain `partial`.
6. Never claim a migration from shared schemas, manifests or documentation alone; executable behavior and regression evidence are required.

## Current first integration

Pytyliki's `vendor/reaper_frontend/` pins upstream Reaper commit `34a5970bbdf0a2bc186233aee6631acdeaeb9904`. It contains the C lexer, expression Pratt parser, AST/token headers and reserved-token catalogue. See the recipient repository's `docs/REAPER_FRONTEND.md` for build commands and its exact scope.
