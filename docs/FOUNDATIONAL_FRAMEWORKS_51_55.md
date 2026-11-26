# Reaper foundational frameworks 51–55

**Status:** executable Reaper reference contracts; enforcement across the entire compiler and repository lifecycle remains partial.  
**Source:** `frameworks/foundation_51_55.rpr`  
**Dependency:** `frameworks/foundation_46_50.rpr`  
**Schema:** `reaper.foundation.eleventh.v1`

## Framework set

| No. | ID | Framework | Responsibility | Maturity |
|---:|---|---|---|---|
| 51 | `foundation.standard.v1` | Standard | Normative, recommended and advisory engineering rules | Partial |
| 52 | `foundation.regulation.v1` | Regulation | Policy controls, severity and bounded exception records | Partial |
| 53 | `foundation.specification.v1` | Specification | Versioned requirements and complete acceptance coverage | Partial |
| 54 | `foundation.schema.v1` | Schema | Typed field definitions, payload checks and compatibility | Partial |
| 55 | `foundation.matrix.v1` | Matrix | Complete row/column coverage and evidence summary | Implemented |

## 51. Standard — rule registry

A rule is:

`[rule_id, domain, level, statement, maturity]`

Levels are normative, recommended and advisory. The module validates catalogued rules, uniqueness and selected rule IDs. The normative subset is available for downstream policy gates. The registry does not itself prove repository compliance.

Public functions: `standard_levels()`, `standard_catalog()`, `standard_validate_rule(rule)`, `standard_validate_catalog()`, `standard_validate_selection(ids)`, `standard_normative_rules()`.

## 52. Regulation — policies and exceptions

A policy uses:

`[policy_id, domain, control, severity, maturity]`

An exception is:

`[policy_id, reason, owner, expires_epoch, status]`

Exception records require a known policy, non-empty reason/owner, positive integer expiry and a declared status. Approval here is metadata only; it does not grant authority or disable host enforcement. Expiry comparison against a real clock remains the responsibility of an external trusted policy service.

Public functions: `regulation_severities()`, `regulation_policies()`, `regulation_validate_policy(policy)`, `regulation_validate_exception(exception)`, `regulation_validate_catalog()`, `regulation_validate_exceptions(exceptions)`.

## 53. Specification — normative requirements

A specification descriptor is:

`[spec_id, version, purpose, requirements, acceptance]`

Each requirement is `[requirement_id, statement, level]`. Each acceptance record is `[requirement_id, evidence_reference]`. IDs must be unique and every requirement must have exactly one acceptance reference.

Public functions: `specification_requirement_levels()`, `specification_validate_requirement(requirement)`, `specification_validate_descriptor(specification)`, `specification_validate_evidence(evidence)`.

## 54. Schema — typed data contract

A schema descriptor is:

`[schema_id, major, minor, fields, allow_trailing_optional_fields]`

Each field is `[field_name, field_type, required]`. The supported kinds include current Reaper runtime values and fixed-width integer labels. Validation checks field names, presence and basic value kinds. Fixed-width integer range checking is not fully lowered by this descriptor-only implementation; the Structure group has the existing u8/i8 range validator.

Compatibility requires the same schema ID and major version. Every required consumer field must exist in the producer schema with the same field type. Unknown/additional fields remain subject to the descriptor's trailing-field policy; this is not a complete binary wire-schema evolution algorithm.

Public functions: `schema_field_types()`, `schema_validate_field(field)`, `schema_validate_descriptor(schema)`, `schema_validate_payload(schema, payload)`, `schema_validate_compatibility(producer, consumer)`.

## 55. Matrix — explicit coverage grid

Matrix statuses are covered, partial, missing and not-applicable. A cell is:

`[row_id, column_id, status, evidence_reference]`

The validator rejects unknown dimensions, duplicate cells and missing cells; the cell count must equal rows × columns. Covered and partial cells require evidence references. The coverage summary returns counts in the order covered, partial, missing, not-applicable, total.

Public functions: `matrix_statuses()`, `matrix_validate_dimensions(rows, columns)`, `matrix_validate_cells(rows, columns, cells)`, `matrix_validate_complete(rows, columns, cells)`, `matrix_coverage_summary(rows, columns, cells)`.

## Unified catalogue

The module exposes `foundation_all_frameworks_55()` and `foundation_validate_catalog_55()`, extending all prior groups to fifty-five unique framework IDs.

## Usage

```reaper
import "../frameworks/foundation_51_55.rpr" as governance

emit governance["foundation_validate_catalog_55"]()
emit governance["standard_normative_rules"]()
emit governance["regulation_validate_exception"](["policy.native-ffi-opt-in", "reviewed trusted library", "security-owner", 1900000000, "proposed"])
emit governance["specification_validate_descriptor"](["spec.runtime.v1", 1, "bounded runtime", [["R-1", "Requests are bounded", "must"]], [["R-1", "tests/test_runtime_platform.py"]]])
emit governance["schema_validate_payload"](["sample.v1", 1, 0, [["name", "text", true]], false], ["Reaper"])
emit governance["matrix_coverage_summary"](["lexer", "parser"], ["syntax", "diagnostics"], [["lexer", "syntax", "covered", "tests/test_lexer.py"], ["lexer", "diagnostics", "partial", "docs/errors/DIAGNOSTICS.md"], ["parser", "syntax", "covered", "tests/test_parser.py"], ["parser", "diagnostics", "missing", ""]])
```

## Verification and safety

Tests validate rule maturity, exception shape/expiry metadata, full requirement acceptance, schema field compatibility and complete matrix coverage. No clock, approval authority, repository policy, CI gate or external standard is automatically enforced by this pure Reaper module.
