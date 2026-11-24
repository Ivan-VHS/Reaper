# Kontexa — Reaper distribution integration

**Product ID:** `jora.app.kontexa`  
**Canonical name:** Kontexa  
**Product boundary:** standalone application package; not a built-in Reaper plugin and not part of the Reaper language runtime.

## Distribution contract

The `kontexa` Python package is installed alongside the Reaper tooling distribution so a user can launch the product with the `kontexa` console command or `python -m kontexa`. It uses only Python's standard library and ships its browser interface as package data (`kontexa/web/*`).

This packaging relationship is a distribution convenience, not a runtime dependency: Kontexa's document engine does not import Reaper modules, access compiler internals, or require Reaper to be running.

## Runtime boundaries

- Local UI and API listen on `127.0.0.1` only.
- Translation provider calls are opt-in and use a user-configured OpenAI-compatible endpoint.
- Remote provider URLs must use HTTPS; plain HTTP is allowed only for loopback endpoints.
- User documents and translation cache remain in the user's local profile. The cache can be disabled or cleared in settings.
- API credentials are process-only by default; persistent storage requires an explicit user setting.
- The package is independent of Reaper's native C17 compiler track and its built-in plugin registry.

## Verification

Run from the repository root:

```bash
python -m unittest discover -s tests -p 'test_kontexa*.py' -v
python -m kontexa --no-browser
```

The Kontexa tests verify the 60,000-character boundary, context-graph construction, reversible Markdown shielding, chunk/cache behavior, terminology locks, numeric checks, provider contract, local API and cross-origin rejection.

## Maturity boundary

The application and local runtime are implemented and tested at alpha quality. Translation quality still depends on the configured model and must be reviewed for legal, clinical, security-critical and contractual use. Tone and semantic audit findings are model-based review signals, not formal proof. The 60,000-character contract is a per-document input limit, not a guarantee that every remote provider will accept the entire document in one model call; Kontexa orchestrates bounded segments through the selected provider.
