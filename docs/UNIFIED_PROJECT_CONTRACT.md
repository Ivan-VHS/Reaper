# Unified project contract v1

| Field | Requirement |
|---|---|
| Capabilities | stable ID, implemented/partial status, evidence path |
| Interfaces | versioned format, direction, peer and opt-in |
| Validation | schema, bounds, repository-local evidence |
| Native ABI | explicit trusted path; no implicit loading |
| Safety | bounded input and project-specific privilege boundary |

Run `python tools/validate_project_contract.py`. Manifest is an inventory, not a wishlist.


## Shared documentation semantics

This project follows the [Ivan-VHS Unified Documentation and Semantics Standard](UNIFIED_DOCUMENTATION_STANDARD.md). Capability maturity, runtime state, verification result and integration policy are separate dimensions. In capability entries, maturity describes implementation progress; terms such as `optional` and `opt_in` describe integration policy and must not be interpreted as maturity.

This addition clarifies documentation semantics only. It does not change the existing project-contract v1 schema, field names or stored values. Any machine-readable schema migration must be versioned and pass the repository's contract validator.

Scenario Flow v1 is registered as a `partial` capability: the reference frontend, tree-walk runtime, Canonical IR/VM and LSP support are implemented, while native C17 and self-hosted frontend parity remain outstanding. See [Scenario Flow v1](SCENARIO_FLOW_V1.md) for grammar, semantics, limits and privilege boundaries.
