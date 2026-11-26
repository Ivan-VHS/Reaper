# Reaper foundational frameworks 36–40

**Status:** executable Reaper reference contracts; complete type/effect semantics and systems syntax remain partial.  
**Source:** `frameworks/foundation_36_40.rpr`  
**Dependency:** `frameworks/foundation_31_35.rpr`  
**Schema:** `reaper.foundation.eighth.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 36 | `foundation.context.v1` | Context | Source/module/locale/phase/target and SourceMap span context | Partial |
| 37 | `foundation.model.v1` | Model | Runtime value categories and typed record descriptors | Partial |
| 38 | `foundation.pattern.v1` | Pattern | Required constructs for reusable engineering patterns | Partial |
| 39 | `foundation.paradigm.v1` | Paradigm | Flow-first, classic, MOST and QCS frontend modes | Partial |
| 40 | `foundation.concept.v1` | Concept | Concept inventory and explicit relation graph | Partial |

## 36. Context — source and execution coordinates

A source context is:

`[source_file, module_id, locale, phase, target_profile]`

Locales and phases are closed catalogues. Source spans use:

`[start_offset, end_offset, line, column]`

A source map is a list of `[source_id, span]` entries. These validators preserve simple ranges but do not claim a complete compiler-wide SourceMap, macro expansion map or cross-file diagnostic remapping.

Public functions: `context_locales()`, `context_phases()`, `context_target_profiles()`, `context_fields()`, `context_validate_descriptor(context)`, `context_validate_span(span)`, `context_validate_source_map(map)`.

## 37. Model — values and typed records

The model distinguishes current runtime value kinds from planned pointer/reference/slice semantics. Record descriptors use:

`[record_id, [[field_name, field_type, mutable], ...]]`

Field names must be unique, fields must have known non-planned types and mutability is explicit. Fixed-width types remain partial as language/compiler declarations even though runtime scalar validators exist elsewhere. No binary struct layout or native ABI lowering is claimed.

Public functions: `model_primitive_types()`, `model_validate_type(type)`, `model_validate_field(field)`, `model_validate_record(record)`, `model_value_kinds()`, `model_validate_runtime_kind(kind)`.

## 38. Pattern — reusable engineering patterns

Patterns identify a domain, required constructs and maturity. Requests are:

`[pattern_id, supplied_constructs]`

The validator ensures every required construct is present and no construct is duplicated. It does not rewrite programs or automatically infer that a codebase follows a pattern.

Public functions: `pattern_catalog()`, `pattern_validate_request(request)`, `pattern_find_by_domain(domain)`.

## 39. Paradigm — language modes

The catalogue distinguishes:
- **flow-first** — Reaper's `::` composition;
- **classic** — existing statement and expression syntax;
- **MOST** — exact localized aliases canonicalized before parsing;
- **QCS DSL** — separate hardware-domain validation frontend;
- **systems syntax** — reserved/planned declarations that are not yet a complete parsed and lowered feature.

Mode selection validates known maturity and unique IDs; it does not guarantee that all modes can be mixed in one file or that QCS expressions execute in the Reaper runtime.

Public functions: `paradigm_profiles()`, `paradigm_validate_profile(id)`, `paradigm_validate_selection(ids)`, `paradigm_validate_interop(source, target)`.

## 40. Concept — shared concept graph

The concept registry links source spans, value models, ownership, capabilities, module graphs, canonical IR, execution lifecycle and target stacks to their owning framework IDs. Relations are explicit and validated against known nodes.

Public functions: `concept_catalog()`, `concept_links()`, `concept_validate_catalog()`, `concept_validate_link(link)`, `concept_find_concept(id)`.

## Unified catalogue

The module exposes `foundation_all_frameworks_40()` and `foundation_validate_catalog_40()`, extending all earlier groups to forty unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_36_40.rpr" as concepts

emit concepts["foundation_validate_catalog_40"]()
emit concepts["context_validate_span"]([10, 18, 2, 4])
emit concepts["model_validate_record"](["gpio.pin.v1", [["pin", "u8", false], ["enabled", "boolean", true]]])
emit concepts["pattern_validate_request"](["module-boundary", ["import", "export", "cycle-check"]])
emit concepts["paradigm_validate_selection"](["flow-first", "classic", "most"])
emit concepts["concept_validate_link"](["concept.value-model", "concept.canonical-ir", "feeds"])
```

## Verification and safety

Tests check context/span bounds, model field uniqueness, pattern requirements, paradigm maturity and concept-link endpoints. These are static contracts and registries. No source code, native layout, compiler mode switch, macro expansion or runtime effect is created by this module.
