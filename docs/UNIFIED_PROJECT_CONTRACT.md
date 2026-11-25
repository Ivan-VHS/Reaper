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

The framework federation entries extend the existing project-contract v1 inventory without changing its schema or field names. They record the twenty framework namespaces, the Reaper module helpers, the bounded host-callback ABI and the evidence paths used to verify each surface. The contract deliberately keeps the 120 domain operation handlers marked partial: signatures are registered, but built-in handlers and Reaper-to-native source bindings are not shipped. Future schema changes must be versioned and pass the repository's contract validator.
