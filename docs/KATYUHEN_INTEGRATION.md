# Katyuhen integration — Reaper

## Role in the ecosystem

Reaper is Katyuhen's language and developer-tooling subsystem. It owns the Reaper language, its Python reference runtime, CLI/REPL, Studio, LSP/DAP services and the versioned native ABI. It is not a replacement for the specialist audio or hardware tools.

## Registered interfaces

| Interface | Direction | State | Boundary |
|---|---|---|---|
| Reaper C ABI v1 | Provides | Partial | Explicitly selected native library; C17 parity is not complete |
| OPlague device snapshot v1 | Consumes | Specified | Read-only, versioned JSON file exchange |
| VentuSample pack v1 | Consumes | Implemented | Manifest metadata audit only |
| Pytyliki C ABI v1 | Consumes | Specified | Optional caller-selected trusted library |

## Integration rules

- Keep Python runtime semantics and the native C17 track independently versioned and tested.
- Never discover or load a native library implicitly through PATH or an untrusted manifest.
- Treat device snapshots as evidence, not authority to change a device or install a driver.
- Treat pack metadata metrics as metadata comparisons, not audio-quality or waveform judgments.
- Keep Reaper useful when every optional peer is absent.

## Workspace and visual identity

Mora is the ecosystem's desktop entry point. Reaper Studio remains a specialist IDE and retains its own editor layout; a native Mora adapter may reuse the semantic tokens from DuckOS's `mora.theme.v1` contract without fetching remote styles at runtime.

The Katyuhen ecosystem registry is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/ecosystem/katyuhen.v1.json). The local project declaration is [integrations/katyuhen/manifest.json](../integrations/katyuhen/manifest.json).

## Validation

Run the existing Reaper test suite and native ABI checks for the selected build. A registry declaration does not count as conformance evidence.
