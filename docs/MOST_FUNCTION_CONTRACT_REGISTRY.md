# MOST / Reaper Function Contract Registry

The registry contains **147 existing specifications + 519 proposals = complete API contract registry**.

| State | Meaning |
|---|---|
| Specified | stable contract exists |
| Implemented | code and tests exist |
| Proposed | future acceptance target |
| Deprecated | retained ID, no new use |

A registry entry is not an implemented function. Use `language/function_registry.v1.json` and the implementation-status ledger as the machine-readable source.

## Architecture category view

The registry now assigns every stable function ID to exactly one of seven architecture categories. The original 13 MOST groups, their order ranges and their names remain unchanged.

See [Psychoporter Engineering Code — function categories](FUNCTION_CATEGORIES_666.md) for the complete grouped list of all 666 entries.

| Category | Count |
|---|---:|
| Kernel, memory and concurrent execution | 121 |
| Reaper language, type system and compiler | 260 |
| Desktop, UI and interaction | 22 |
| Networking and distributed systems | 21 |
| Storage, schemas and data | 121 |
| Security, trust and resilience | 100 |
| Ecosystem, integrations and maintenance | 21 |
| **Total** | **666** |

The validator enforces complete coverage, unique category ownership per original group, entry-to-group consistency and exact category totals. Categorization is metadata only: it does not promote implementation status or claim native MOST callability.
