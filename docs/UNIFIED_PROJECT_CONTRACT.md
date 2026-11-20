# Unified project contract v1

This repository participates in the Ivan-VHS project ecosystem. The unified contract makes three independent products discoverable through one stable, evidence-backed description without forcing them into one runtime or pretending that unfinished roadmap items already work.

## Contract files

- `project-contract.json` is this repository's local capability and integration manifest.
- `schemas/unified-project-contract.v1.schema.json` defines the shared JSON shape.
- `tools/validate_project_contract.py` validates the manifest using only the Python standard library.
- `.github/workflows/project-contract.yml` runs the validator on relevant pushes and pull requests.

Run the same check locally:

```bash
python tools/validate_project_contract.py
python tools/validate_project_contract.py --json
```

## Shared model

Every project uses the same root fields: `schema`, `project`, `implementation`, `capabilities`, `interfaces`, `integrations`, `safety_boundaries`, and `extension_points`.

Capability identifiers are stable, lowercase, machine-readable names. Each capability has exactly one current implementation status:

- `implemented`: working code exists and the manifest links to its source or tests.
- `partial`: a bounded implementation exists, but the summary states its current limits.

The manifest is an inventory, not a wishlist. Planned work stays in the roadmap and is not counted as implemented capability. Evidence paths must resolve to files in the same repository; missing or unsafe paths fail validation.

## Interoperability rules

The ecosystem preserves independent project boundaries and connects them through explicit, versioned interfaces:

| Producer / consumer | Contract | Transport |
|---|---|---|
| Pytyliki | `pytyliki.c-abi.v1` | Explicit, trusted native-library path |
| OPlague → Reaper | `oplage.device-snapshot.v1` | Versioned JSON file |
| OPlague batch inspector | `oplage.inspection-bundle.v1` | Canonical JSON report |

An integration entry records the peer project, interface, transport, current status, and whether a caller must opt in. Optional native FFI is never loaded implicitly. Consumers must validate schema/version and treat imported data as untrusted input.

## Engineering guarantees

1. **Unified, not monolithic:** shared contracts and naming, independent domain implementations.
2. **Modular and extensible:** capabilities and interfaces are independently versioned; new adapters do not silently change existing contracts.
3. **Evidence-led:** status is backed by repository paths; partial implementations remain explicitly partial.
4. **Consistent and interoperable:** the same manifest structure and validator are used by all participating repositories.
5. **Cross-platform by declaration:** runtime and desktop platform support are listed separately; an interface does not imply every product feature works on every OS.
6. **Safe by default:** read-only discovery, bounded processing, explicit native loading, and clearly stated privilege boundaries remain project-specific requirements.
7. **Reviewable:** CI rejects malformed manifests, duplicate identifiers, unsafe evidence paths, missing files, unknown peers, and invalid integration declarations.

## Change policy

When adding a capability, add its stable identifier, truthful status, concise behavior summary, and evidence paths to `project-contract.json`. When changing an external interface, preserve the old version for compatibility or introduce a new versioned identifier. Update the relevant implementation tests and integration documentation in the same change.

Do not use broad labels such as “universal” or “compatible” as proof of support. Record concrete targets, transports, constraints, and evidence instead.
