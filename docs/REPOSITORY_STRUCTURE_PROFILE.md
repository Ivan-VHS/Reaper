# Repository Structure Profile — Reaper

**Normative reference:** [Ivan-VHS Repository Structure Standard](https://github.com/Ivan-VHS/DAK/blob/main/docs/REPOSITORY_STRUCTURE_STANDARD.md).

This profile applies the shared structure to the Reaper language, compiler/runtime and tooling repository. It preserves the language's own source layout and does not prescribe a generic `src/core` tree.

## Canonical layout

| Concern | Existing canonical location | Responsibility |
|---|---|---|
| Public project entry | `README*.md`, `LANGUAGE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` | Language identity, supported workflows and contribution/security policy |
| Architecture and specifications | `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/INFORMATION_ARCHITECTURE.md`, `docs/UNIFIED_PROJECT_CONTRACT.md` | Architecture, ownership, language/runtime contracts and navigation |
| Reaper language/runtime | `reaper/`, `language/`, `stdlib/`, `frameworks/` | Reference implementation, language metadata, standard library and first-party frameworks |
| Native implementation | `src/`, `include/` | Native compiler/runtime components and exported C interfaces |
| Tool integrations | `editors/`, `applications/`, `tools/`, `harvest/` | Editor support, applications, developer tooling and bounded source bundles |
| Verification | `tests/`, `examples/` | Unit/integration/regression coverage and executable language examples |
| Machine contracts | `schemas/`, versioned registries under `language/`, root project contracts | Stable schemas, token/function registries, ABI and cross-project contracts |
| Reproducible tooling | `scripts/`, `Makefile`, `CMakeLists.txt` | Build, validation and maintenance entry points |
| CI | `.github/workflows/` | Language, native build, contract, security and documentation gates |

## Domain separation

- Reaper source files and their canonical IR, Span/SourceMap and DABI contracts are the authority for language semantics.
- The Python reference runtime, native C implementation and editor integrations must remain separately identified by role and maturity. A planned native capability is not treated as shipped merely because a registry or design document names it.
- Reciprocal Pytyliki work is governed by versioned ABI/contracts and cross-repository tests; changes to one side must be assessed against the other.
- Examples are executable specifications only to the extent that CI actually runs them.

## Formal evidence

The repository's parser/compiler/runtime tests, typed registries, ABI declarations and deterministic fixtures provide executable evidence. A separate proof-assistant tree is optional and must not be represented as present until proof sources and a reproducible checker are integrated.

## Change rule

Any source relocation must update package imports, CMake targets, editor/build integrations, registries, schema references, tests, documentation links and CI path filters together. Preserve existing canonical paths until that complete migration is reviewed.
