# Quality, Repeatability and Native Integration

## Quality
The language pipeline must report source locations, preserve useful diagnostics and reject invalid programs without corrupting interpreter state. Public features need focused tests and explicit failure semantics.

## Repeatability
Lexing, parsing, lowering and optimization must produce stable outcomes for equivalent inputs. Repeated executions should not leak state between programs; transformations must be safe to replay or explicitly document their side effects. Batch or federated work must define bounds, ordering and partial-failure behavior.

## Native integration
Keep the C11 lexer/parser/IR front end and Python 3.10+ runtime aligned through explicit contracts. Native APIs should expose stable types and ownership boundaries. Editor, CLI, embedded and polyglot integrations should preserve source locations and diagnostics instead of hiding them behind lossy wrappers.

## Reaper application
Prioritize deterministic front-end stages, stable token and IR contracts, reproducible optimizer passes, runtime isolation, CLI/editor interoperability and a narrow native FFI. Feature-registry or syntax changes must update tests, documentation and generated catalogs together.

## Acceptance and evidence
quality-repeatability-native.v1.json records implementation and verification evidence for every criterion. The validator checks manifest structure, unique IDs and evidence-path existence; it does not replace the language test suite, native C tests, package build, editor checks or runtime conformance tests.

Use implemented only when code and a maintained test or workflow support the requirement. Use planned for incomplete work. Use not_applicable only with a written reason.

Local checks: python tools/validate_quality_repeatability_native.py --self-test and python tools/validate_quality_repeatability_native.py --json.
