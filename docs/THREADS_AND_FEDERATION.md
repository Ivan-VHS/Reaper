# Reaper — project-thread integration ledger

This ledger consolidates the Reaper-related requirements discussed across repository, МОСТ, native-core, design-system, consent and federation threads. It separates verified implementation from proposals.

## Implemented and source-backed

| Requirement family | Current implementation | Evidence |
|---|---|---|
| Flow-first language and runtime | Lexer, parser, interpreter, CLI, REPL and modules | `reaper/lexer.py`, `reaper/parser.py`, `reaper/runtime.py`, `reaper/cli.py` |
| Reaper Studio | Editor, check/run/debug, breakpoints, variables, call stack and theme controls | `reaper/desktop.py` |
| МОСТ / Russian-native surface | Canonical aliases, token catalogues, syntax profile and implementation-status ledger | `language/most_keyword_aliases.json`, `language/most_russian_native_profile.json`, `docs/MOST_IMPLEMENTATION_STATUS.md` |
| Native compiler track | Native C17 lexer/parser/AST/IR and selected lowering; Python remains the reference runtime | `src/`, `include/reaper/`, `docs/C_MIGRATION.md` |
| 666-function registry and 20×20 matrix | Traceable contracts and matrices; proposals are distinguished from executable functions | `language/functions_666.json`, `language/most_matrix_20x20.json`, `docs/MOST_IMPLEMENTATION_STATUS.md` |
| Consent and bounded execution | HMAC-authenticated scope grants, TTL/revocation, quotas, deterministic cleanup and audit | `reaper/governance.py`, `reaper/resources.py`, `reaper/audit.py` |
| Embedded C and QCS | Reference MCU project helpers and separate QCS parser/validator; no hardware flashing claim | `reaper/embedded.py`, `reaper/qcs.py` |
| Design-system threads | Semantic light/dark palette, visible status, keyboard access and reduced-motion support | `reaper/ui_theme.py`, `reaper/ui_motion.py` |
| Vertical self-product | Deterministic, bounded repeated transformation passes | `reaper/self_product.py`, `tests/test_self_product.py` |

## Federation

- OPlague → Reaper: implemented, bounded `oplage.device-snapshot.v1` JSON input.
- Reaper → OPlague: implemented, read-only `reaper.oplage-comparison.v1` report.
- Reaper → Pytyliki: implemented, explicit trusted-path `pytyliki.c-abi.v1` FFI.
- VentuSample → Reaper: partial, pack export exists but a Reaper consumer is not implemented.
- Reaper → VentuSample: planned render-request adapter.

See [OCTA-8](OCTA_PYRAMID_FEDERATION.md) and the [four-project federation matrix](PROJECT_FEDERATION_MATRIX.md).

## Deliberate boundaries

- The 666 catalogue includes specifications and proposals; it does not mean 666 callable functions are complete.
- Native C17 support is partial; Python remains the compatibility reference until parity is demonstrated.
- In-process FFI runs trusted native code and is not a sandbox for untrusted extensions.
- Embedded project helpers do not flash devices or claim live hardware debugging.
- The OCTA apex is metadata, never a central runtime dependency.

## Repositories

[Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [OPlague](https://github.com/Ivan-VHS/OPlague) · [VentuSample](https://github.com/Ivan-VHS/VentuSample)
