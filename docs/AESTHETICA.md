# AESTHETICA — dual-axis aesthetic analysis

**Version:** 1.0.0  
**Source module:** `frameworks/aesthetica/core.rpr`  
**Executable example:** `examples/aesthetica.rpr`  
**Maturity:** Partial — reference-runtime module and acceptance example; no native C17 parity or Studio integration is claimed.

## Purpose

AESTHETICA models aesthetic evidence without reducing beauty and ugliness to opposite ends of one scale. An object may have high scores on both axes: deliberate dissonance, irregularity, grotesque form or unresolved tension can be expressive rather than defective.

The framework is an explainable evaluation aid. It does not determine universal beauty, diagnose an observer, infer culture from appearance, or replace human review. Scores are contextual heuristics whose meaning depends on the declared perspective, purpose, culture tag, evidence and dimension weights.

## Current Reaper language boundary

The module uses only the currently executable Reaper reference grammar: `export`, `craft`, `make`, `vary`, `change`, `when`, `otherwise`, `each`, `yield`, lists, indexing and supported built-ins.

The current language surface does not provide executable user-defined `record`, `enum`, `interface`, generic `Result<T, E>`, or a first-class `Span` value in this module. The implementation therefore uses documented list contracts and an explicit `["ok", payload]` / `["err", diagnostic]` envelope. Source positions are caller-provided provenance tuples; they are not represented as compiler-generated Span objects or SourceMap entries.

No `Shell`, logging host, filesystem, network, clock, FFI or hardware capability is used.

## Public data contracts

All list positions are zero-based when accessed from Reaper code.

### Evidence

```text
[
  axis,             # "beauty" | "ugliness"
  dimension,        # one of the dimensions below
  score,            # finite number in [0, 1]
  confidence,       # number in [0, 1]
  salience,         # number in [0, 1]
  intent,           # "deliberate" | "accidental" | "unknown"
  explanation,      # non-empty text
  source_span       # [source, start_line, start_col, end_line, end_col]
]
```

Supported dimensions:

- `harmony`
- `proportion`
- `contrast`
- `coherence`
- `complexity`
- `originality`
- `expression`
- `functionality`
- `context_fit`
- `emotional_impact`
- `imperfection`
- `intentional_tension`

### Weight profile

A weight entry is `[dimension, weight]`, with a unique dimension and a weight in `[0, 1]`. At least one weight must be positive. Every dimension used by evidence must have a corresponding weight entry.

### Context

```text
[perspective_id, purpose, culture_tag]
```

All three fields are non-empty text values except that `culture_tag` may be empty when no cultural context is being asserted. The current evaluator validates the field types and requires a non-empty perspective and purpose. The fields are labels supplied by the caller, not inferred attributes.

### Stage

```text
[code, start_step, end_step, state_label, summary]
```

Stages must have unique codes, non-empty labels and summaries, non-negative numeric boundaries, and strictly positive duration. A stage list must be ordered and contiguous: each stage starts exactly where the previous stage ends.

## API

The module exports:

| Export | Behavior |
|---|---|
| `API_VERSION` | Module version string |
| `REPORT_SCHEMA` | `aesthetica.report.v1` |
| `EVOLUTION_SCHEMA` | `aesthetica.evolution.v1` |
| `DIAGNOSTIC_SCHEMA` | Diagnostic envelope identifier |
| `validate_evidence(item)` | Validates a single evidence tuple |
| `validate_weights(weights)` | Validates dimensions, uniqueness and weight bounds |
| `validate_evidence_set(evidence, weights)` | Validates a non-empty evidence list and its weight coverage |
| `aggregate_axis(evidence, weights, axis)` | Returns `[score, confidence, evidence_count]` |
| `aggregate_dimension(evidence, weights, dimension)` | Computes a confidence/salience/weight-adjusted dimension score |
| `recommended_action(item)` | Preserves deliberate distortion; reviews unknown intent; refines accidental ugliness |
| `evaluate(object_id, context, evidence, weights)` | Creates an explainable, versioned report |
| `compare_profiles(before, after, threshold)` | Compares two reports for the same object identity |
| `verify_stage(stage)` | Validates one pipeline stage |
| `verify_stages(stages)` | Validates unique stage codes and contiguous ordering |
| `success(payload)`, `failure(code, message, span)` | Explicit result envelopes |

### Report shape

```text
[
  "aesthetica.report.v1",
  object_id,
  perspective_id,
  purpose,
  culture_tag,
  beauty_axis,       # [score, confidence, evidence_count]
  ugliness_axis,     # [score, confidence, evidence_count]
  contrast_score,
  duality_tension,
  coexistence,
  dimension_coverage,
  expressive_power,
  findings
]
```

Each finding contains its axis, dimension, recommended action, declared intent, original score/confidence, explanation and supplied source span. A finding is evidence, not an automatic edit instruction.

### Diagnostic envelope

```text
["err", [
  "aesthetica.diagnostic.v1",
  "AES-E###",
  "error",
  message,
  source_span
]]
```

When the caller has not supplied a usable source span, the framework reports the stable fallback span `["<aesthetica>", 1, 1, 1, 1]`. This fallback must not be mistaken for a parser Span.

## Scoring model

For evidence item (i), the base weight is:

[
b_i = salience_i \times confidence_i \times dimensionWeight_i
]

The axis score is the weighted average:

[
A = \frac{\sum_i score_i \times b_i}{\sum_i b_i}
]

Confidence is aggregated separately and does not erase the distinction between the two axes. Missing evidence for an axis produces a zero score and zero confidence rather than fabricating observations.

Contrast is calculated from evidence whose dimension is `contrast`. The duality model then uses:

[
coexistence = \min(beauty, ugliness)
]

[
tension = coexistence \times contrast
]

Coverage is the number of distinct observed dimensions with positive weights divided by the number of enabled dimensions.

The current expressive-power heuristic is:

[
0.30B + 0.25U + 0.20C + 0.15T + 0.10Coverage
]

where (B) is beauty, (U) is ugliness, (C) is contrast and (T) is duality tension. The coefficients are transparent defaults, not empirically validated universal constants. Callers should version their weight profile and retain the full evidence when comparing reports.

Profile stability compares the beauty, ugliness and contrast coordinates for two reports with the same object ID:

[
stability = 1 - \frac{|\Delta B| + |\Delta U| + |\Delta C|}{3}
]

The caller supplies the threshold. This is aesthetic-profile stability, not object identity, semantic equivalence or proof that a design change is safe.

## Intentional imperfection policy

| Declared intent | Axis | Recommendation |
|---|---|---|
| deliberate | either | `preserve` |
| unknown | either | `review` |
| accidental | ugliness | `refine` |
| accidental | beauty | `clarify` |

AESTHETICA does not modify source objects. It returns findings only. Any future generative adapter must be separately authorized, produce a new revision, preserve the original, and make the diff reviewable.

## Run

From the repository root:

```sh
python -m reaper --check examples/aesthetica.rpr
python -m reaper examples/aesthetica.rpr
```

Expected final output line:

```text
AESTHETICA_OK
```

The executable example covers successful dual-axis evaluation, deliberate imperfection preservation, accidental inconsistency recommendations, score-range rejection, duplicate-weight rejection, same-object revision comparison, different-object rejection, and stage timeline validation.

## Maturity gates

The reference-runtime implementation is **Partial** until CI executes the acceptance example on every supported Python version. It remains Partial after that gate until all of the following exist:

1. A typed, versioned Reaper-level data model and structured `Result`/diagnostic types, without pretending reserved syntax is implemented.
2. Compiler-generated source spans and source maps wired into the module's findings.
3. Native C17 support or an explicit, documented unsupported boundary with conformance fixtures.
4. Studio/LSP presentation using the same reports and diagnostics.
5. Versioned profile serialization, deterministic compatibility rules and regression fixtures.
6. Integration adapters for other Reaper products, each with explicit contracts and independent acceptance tests.

Do not label AESTHETICA as an AI, psychological instrument or universal aesthetic oracle. The delivered scope is a deterministic, evidence-carrying scoring framework over caller-supplied observations.
