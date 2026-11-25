# Internationalization and language support

**Status:** shared i18n contract v1 and starter catalogs. This establishes runtime-independent language negotiation and CI coverage; it does not claim that every screen or every human language has already been professionally translated.

## Goal

Support every well-formed BCP 47 language tag and every script/orthography that the active Unicode, font, input-method and platform stack can represent. Do not hardcode a finite list of human languages. A language pack adds translations; it must not be required merely to open, edit or exchange text in that language.

## Normative baseline

- Language tags: [BCP 47 / RFC 5646](https://www.rfc-editor.org/rfc/rfc5646).
- Character repertoire and text processing: [Unicode 18.0](https://www.unicode.org/versions/Unicode18.0.0/).
- Locale data and formatting rules: [Unicode CLDR 49](https://www.unicode.org/reports/tr35/).
- Encoding: UTF-8 internally and in files, with explicit UTF-16 conversion only at platform APIs that require it.
- Catalogs: stable message ids, locale-tagged resources, explicit translation status and fallback.

The manifest records Unicode 18.0 and CLDR 49 as the current reference baseline. Runtime formatting must use the newest compatible platform ICU/CLDR data; do not freeze date, currency, plural or collation rules into hand-written tables.

## Language resolution

1. Read an explicitly selected language tag.
2. Otherwise derive the tag from the operating system/user preference.
3. Canonicalize the tag with the platform BCP 47 implementation, retaining the user's preference.
4. Search the exact tag, script parent, language parent, then the source locale.
5. Resolve each missing message by its stable id and continue the fallback chain.
6. Never silently replace an invalid or unavailable pack with an unrelated language; report the fallback state.

Examples: `zh-Hant-TW → zh-Hant → zh → en`, `sr-Latn-RS → sr-Latn → sr → en`. A well-formed tag absent from the built-in catalog remains selectable: formatting and text input follow the platform locale, while untranslated UI messages use the declared fallback.

## Text and layout requirements

- Preserve Unicode scalar values. Normalize user-facing comparison/search boundaries to NFC where safe; never rewrite source files, user documents, code identifiers, paths or hashes merely to normalize them.
- Use grapheme-cluster boundaries for cursor movement, deletion, selection and truncation. A visible character is not necessarily one code point.
- Support IME composition, dead keys, alternate keyboard layouts, combining marks, contextual shaping, ligatures, mixed-direction text and bidi isolation for interpolated values.
- Derive direction from locale/script metadata. Use logical layout properties; never mirror semantic icons or charts blindly.
- Provide font fallback per script and test CJK, Arabic, Hebrew, Devanagari, Thai, Hangul and extended Latin/Cyrillic text. Do not bundle unlicensed fonts.
- Respect locale-specific plural categories, calendar, week start, numbering system, decimal/group separators, currency placement, units, collation and relative time through platform CLDR services.
- Keep machine protocols invariant: JSON keys, diagnostic codes, API names, file formats, ABI symbols, command names, hashes and serialized numeric values are not localized.

## Translation contract

- `en` is the source catalog in v1. Starter translations are supplied for `ru`, `uk`, `zh-Hans` and `ar`.
- `complete` means every source message id in this catalog set has a non-empty translation; it does not mean the whole application UI is translated.
- New UI strings must use stable message ids rather than inline concatenation or language-specific conditionals.
- Keep placeholders stable and reorderable. Use ICU MessageFormat/CLDR plural rules in adapters; do not concatenate translated sentence fragments.
- Human-reviewed translations are the release standard. Machine-draft text must be marked as such and cannot be promoted to `complete` without review.
- Language packs are local-first, versioned and explicit. No automatic cloud translation, telemetry of typed text or network dependency is permitted.

## Project integration boundary

Reaper's source language is not translated when the UI language changes. Keyword aliases remain explicit grammar features, and all diagnostics keep stable `RPR-*` codes. Unicode identifiers must use the language's identifier rules and must not be case-folded as ordinary prose.

| Project | Native integration contract |
|---|---|
| DuckOS | Reaper-owned native locale service; Mora host shell uses browser `Intl` and the same catalog ids |
| Reaper | Locale-aware diagnostics/editor UI; language grammar, canonical IR, ABI and diagnostics codes remain stable |
| Pytyliki | UTF-8 C11 core; explicit UTF-16 Win32 boundary; locale-neutral CLI and JSON |
| VentuSample | Qt 6 `QLocale`/`QTranslator`; real-time audio and preset serialization remain locale-neutral |
| OPlague | Local Python/Tk catalog adapter; machine-readable inspection contracts stay invariant |

Runtime adapter: The language service and editor/CLI diagnostics resolve stable RPR diagnostic codes to localized message ids. Grammar, canonical IR, Span, ABI symbols and serialized forms remain locale-independent.

## Validation

Run:

```sh
node tools/check_i18n.mjs
```

The GitHub Actions workflow runs the same check on every change to the catalog contract. It validates BCP 47 tags, catalog metadata, source-key coverage for catalogs marked complete, Unicode-safe strings and platform locale formatting services. Product CI must additionally add UI tests for RTL layout, font fallback, IME composition, grapheme editing, accessibility names and locale switching in each native frontend.

## Adding a language

1. Add a canonical BCP 47 tag to `i18n/manifest.v1.json`.
2. Add the locale entry and reviewed messages to `i18n/catalogs.v1.json`.
3. Mark it `partial` until all source ids are translated and reviewed; only then mark it `complete`.
4. Run the validator and add representative script/RTL/formatting tests in the owning product.
5. Never change stable message ids or protocol fields to match a translation.

A locale is supported by the platform contract even when its UI translation pack is not yet complete.
