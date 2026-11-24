# Kontexa

**Kontexa** is a context-first translation workspace for long technical, legal, analytical and Markdown documents. Its per-document input limit is **60,000 Unicode code points**, including spaces and markup.

The application is a separate product with its own name and package identity. It is distributed as a Python package in the Reaper toolchain repository, but it is not registered as a Reaper built-in plugin and does not depend on the Reaper language runtime.

## Implemented in this release

- Desktop-first local web workspace with import/export for Markdown and text.
- Strict 60,000-character input validation, including the exact boundary.
- Markdown-aware block and sentence chunking with exact source reconstruction.
- Reversible Structural Shield for fenced code, inline code, HTML tags/comments, template variables, placeholders, links and structural Markdown markers.
- Whole-document context graph (section nodes, terminology nodes and relationships), a per-segment context passport, and rolling memory over the previous five segments.
- Glossary suggestions and manual rules: hard lock, preferred translation and do-not-translate.
- OpenAI-compatible provider adapter; supports hosted HTTPS endpoints and loopback HTTP endpoints such as local model servers.
- SQLite translation cache with chunk, neighbouring-context, language, glossary, style, provider and document-identity keys. A changed segment and its immediate neighbours are invalidated; unaffected chunks can be reused.
- Post-translation checks for protected tokens, numeric/unit markers, glossary locks and heuristic negation/reference warnings.
- Optional back-translation and tone-drift audit with a register score, plus on-demand 2–3 alternative translations for ambiguity flags.
- Optional per-segment back-translation semantic audit for omissions, polarity, quantities, obligations and conditions; findings remain review signals, not formal proof.
- Local history in browser storage and machine-readable quality report.
- Cancellable background jobs and progress updates.
- No third-party Python runtime dependencies.

## Run

Python 3.10 or newer is required.

```bash
python -m kontexa
```

Or install the standalone package first:

```bash
python -m pip install .
kontexa
```

The application opens at `http://127.0.0.1:8765`. Stop it with `Ctrl+C`.

Optional arguments:

```bash
python -m kontexa --port 9000
python -m kontexa --no-browser
```

When installed from the project, the same launcher is available as:

```bash
kontexa
```

## Configure a translation provider

Open **Настройки движка** and configure:

- **API Base URL** — for example `https://api.example.com/v1`, or a loopback local server such as `http://127.0.0.1:11434/v1`.
- **Model ID** — the exact model identifier accepted by that server.
- **API key** — optional for local keyless providers. For remote providers use the key required by that provider.

The API key is held in process memory by default. Enable **Сохранить API-ключ** only when you explicitly want it stored in your local user configuration directory. On POSIX systems the config file is created with mode `0600` where supported. Remote providers must use HTTPS; plain HTTP is accepted only for loopback addresses.

Kontexa sends text only to the provider configured by the user. The local application itself binds to `127.0.0.1`, rejects cross-origin API requests, and does not expose the configured key through its read API. Review your selected provider's data-handling policy before translating confidential material.

## Verification

From the repository root:

```bash
python -m unittest discover -s tests -p 'test_kontexa*.py' -v
```

The current test suite covers the exact 60,000-character boundary, Unicode counting, document graph generation, structural shielding, Markdown reconstruction, long-paragraph splitting, glossary extraction, number normalization, contextual cache reuse, semantic audit, provider contract, local HTTP service and cross-origin rejection.

## Important quality boundaries

- `Structural Shield` integrity and numeric-marker checks are deterministic invariants. A mismatch prevents a clean result and is surfaced in the report.
- Ambiguity, pronoun-reference and negation checks are heuristics. They are review signals, not proof of semantic correctness.
- A successful HTTP/API call does not guarantee a correct translation. Human review is required for legal, clinical, safety-critical and contractual material.
- The product does not claim a 99% semantic accuracy rate. Quality depends on the selected model, domain, glossary and review process.
- Delta caching is context-aware but not a claim of perfect semantic dependency analysis. The first 1,200 characters, document headings and adjacent chunks are included in cache identity; edits elsewhere may still require a full retranslation when the document's meaning changes globally.
- No credentials are bundled in the source tree.

## Package identity

- Product: **Kontexa**
- Package ID: `jora.app.kontexa`
- Slug: `kontexa`
- Application API: local HTTP loopback v1
- Primary language: Python (stdlib-only service) + HTML/CSS/JavaScript frontend
