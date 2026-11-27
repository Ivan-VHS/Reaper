# Mathematical Research Contracts v1

**Status:** typed catalog and bounded call-plan validator implemented  
**Canonical language contract owner:** Reaper  
**Native computational-kernel owner:** Pytyliki  
**Contract:** `reaper.mathematical-research-contracts.v1`  
**Kernel ABI namespace:** `pytyliki-research-math-c11-v1`  
**Coverage:** 17 problem areas × 3 functions = 51 function contracts

## Purpose

This package gives Reaper a typed, versioned mathematical-research interface for the C11 computational kernels provided by Pytyliki.

Reaper owns the stable function IDs, argument type descriptions, input constraints, result descriptions, effect classifications, resource budgets and evidence policy. Pytyliki owns the native C implementation. The catalog maps each Reaper function ID to its exact Pytyliki C symbol.

This release prepares and validates kernel call plans. It does **not** load a native library, invoke the 51 mathematical symbols, produce a proof object, or claim a mathematical conjecture has been proved. The existing generic Pytyliki C ABI bridge is a separate integration surface; these research symbols are not yet exported by that ABI.

## The 17 mathematical domains

Each domain has three dedicated operations. Exact finite checks, numerical approximations and bounded searches are classified separately.

| # | Problem | Function 1 | Function 2 | Function 3 |
|---:|---|---|---|---|
| 01 | Riemann Hypothesis | Dirichlet partial sum | Eta partial sum | Critical-line residual approximation |
| 02 | P vs NP | CNF validation | SAT assignment verification | Budgeted SAT model search |
| 03 | Collatz | Exact uint64 step | Bounded trajectory | Bounded stopping time |
| 04 | Navier–Stokes | Grid divergence | Grid vorticity | CFL time-step estimate |
| 05 | Birch–Swinnerton-Dyer | Curve nonsingularity mod p | Point count mod p | Frobenius trace mod p |
| 06 | Hodge | Hodge bidegree condition | Cycle-span rank mod p | Candidate span membership mod p |
| 07 | Yang–Mills mass gap | U(1) plaquette phase | Wilson single-plaquette action | Correlator effective-mass estimate |
| 08 | Goldbach | uint64 primality | Pair witness verification | Budgeted pair search |
| 09 | Twin Primes | Pair verification | Budgeted next-pair search | Finite pair count |
| 10 | Halting Problem | Abstract VM step | Fuel-bounded VM run | Trace-transition verification |
| 11 | Hadwiger–Nelson | Finite unit-distance graph | Coloring verification | Budgeted graph coloring |
| 12 | Inscribed Square | Point-to-polyline check | Candidate square verification | Sampled polygonal search |
| 13 | Legendre | Exact square interval | Prime witness verification | Budgeted interval search |
| 14 | Beal | Checked integer-power equality | Common prime-factor search | Candidate counterexample screen |
| 15 | Perfect Cuboid | Exact cuboid check | Face-diagonal roots | Budgeted edge search |
| 16 | Tate | Frobenius fixed-vector check | Invariant-space dimension | Cycle-vector rank mod p |
| 17 | Matrix exponent ω = 2 | Dense matrix product | Product verification | Empirical two-size scaling estimate |

The full machine-readable argument and result descriptors are in `language/mathematical_research.v1.json`. A byte-identical packaged copy is shipped as `reaper/mathematical_research.v1.json`; the test suite checks that the copies remain synchronized. JSON Schema: `schemas/mathematical-research-contracts.v1.schema.json`.

## Python reference API

`reaper/research_math_contracts.py` provides:

| Function | Responsibility |
|---|---|
| `load_research_math_catalog()` | Loads and validates the packaged catalog |
| `find_math_kernel(function_id)` | Resolves one stable function ID |
| `prepare_math_kernel_call(function_id, arguments)` | Validates argument types, exact names, scalar ranges, collection bounds and cross-field shapes; returns an immutable call plan |
| `validate_catalog_document(document)` | Validates ownership, catalog structure, unique IDs, effect classes and evidence policy |
| `validate_pytyliki_kernel_manifest(manifest)` | Checks that Pytyliki publishes the exact 51 catalog IDs and C API names |

A call plan has:

- `execution_performed = false`;
- `claim_status = EXPERIMENTAL_EVIDENCE_ONLY`;
- the exact Pytyliki C symbol;
- normalized, immutable arguments;
- the result type, effect class and evidence class.

The planner refuses missing or extra arguments, Boolean values masquerading as integers, NaN/infinite numeric values, invalid primes, malformed vector/matrix shapes, invalid SAT offsets, grid-size mismatches, out-of-range graph edges and invalid abstract-VM instruction references.

## Effect and evidence classes

| Effect | Meaning |
|---|---|
| `pure_exact` | Exact finite arithmetic, structural or finite-field check |
| `pure_numeric` | Deterministic numeric calculation |
| `finite_numeric` | Floating-point or discretized model computation |
| `bounded_search` | Search constrained by an explicit candidate, node, term, step or fuel budget |

These effects describe the planned computational operation. They do not grant operating-system, device, network or hardware privileges.

## Mathematical claim policy

The following labels are prohibited for results produced solely by this workbench:

- `PROVED`
- `DISPROVED`
- `SOLVED`

Accepted evidence descriptions distinguish:

1. exact finite witness;
2. exhaustive search over a fully declared finite domain;
3. bounded search with unexplored candidates remaining;
4. floating-point approximation;
5. finite-grid numerical diagnostic;
6. simplified physical or lattice model;
7. empirical timing measurement.

A missing witness under an exhausted budget is not a counterexample. A bounded search that returns `LIMIT` has not exhausted its domain. A numerical residual is not a proof of a zero. An empirical scaling estimate is not an asymptotic complexity result.

The Halting Problem is handled separately: general undecidability is already proved. The bounded two-counter executor validates individual finite runs and traces; it is not a general halting decider.

## Ownership and cross-repository flow

```text
Pytyliki C11 research kernels
    ├── 51 stable C symbols
    ├── fixed-width and bounded inputs
    ├── explicit status codes and caller-owned outputs
    └── pytyliki.mathematical-research-kernels.v1.json
                 │
                 │ stable ID + C symbol agreement
                 ▼
Reaper canonical research catalog
    ├── versioned type/argument/effect/evidence contracts
    ├── strict call-plan validation
    ├── source and budget provenance requirements
    └── future opt-in native marshalling adapter
```

No implicit loading of a shared library is performed by the planner. Native dispatch must be a separately reviewed, explicitly opt-in integration that validates ABI version, function availability, buffer lengths, output ownership, return statuses and provenance.

## Resource boundaries

The native kernel limits are part of the Pytyliki contract and are mirrored in the Reaper catalog:

- Riemann sums: at most 1,000,000 terms.
- SAT: at most 24 Boolean variables and 2²⁴ candidate assignments.
- 3D finite-difference grids: at most 1,000,000 cells.
- Elliptic-curve point counting: prime p ≤ 1,000,003.
- Finite-field linear algebra: at most 64 dimensions.
- Dense matrices: at most 128 × 128.
- Unit-distance graph: at most 128 vertices.
- Inscribed-square sampling: at most 128 points.
- Perfect-cuboid search: edge bound ≤ 100,000 and an explicit node budget.
- Beal common-factor trial division: bounded trial factors through 1,000,000, followed by a primality check; unresolved composite cases return a limit status.

The caller must still supply valid storage for every C pointer and out-parameter at the native boundary. A plan is not a buffer allocation.

## Tests and build

The dedicated tests are in `tests/test_research_math_contracts.py`. Reaper CI compiles the package and runs the full unittest discovery suite. The focused cases cover:

- exactly 17 areas and 51 unique functions;
- package catalog equality with the canonical language catalog;
- call-plan construction without falsely claiming execution;
- invalid scalar, prime, non-finite and missing argument rejection;
- SAT offset and assignment validation;
- finite-grid shape checking;
- proof-claim policy rejection;
- manifest agreement and order-sensitive catalog drift detection.

The Pytyliki native engine and C test executable are tested separately in its CMake/CTest pipeline. Passing Reaper catalog tests cannot substitute for Pytyliki native tests, and vice versa.

## Current maturity

| Layer | Status |
|---|---|
| Stable domain and function IDs | Implemented |
| 51 typed catalog records | Implemented |
| JSON Schema | Implemented |
| Reaper catalog and call-plan validator | Implemented |
| Scalar and cross-argument validation | Implemented |
| Pytyliki C11 function implementations | Added; native CI pending |
| Pytyliki CMake/CTest registration | Added; full repository CI pending |
| Research functions exported through Pytyliki C ABI | Not yet implemented |
| Reaper-to-Pytyliki native dispatch for these functions | Not yet implemented |
| Formal proof kernel / machine-checkable proof objects | Not implemented |
| Proofs of the listed open conjectures | Open mathematical research |

The purpose of this boundary is to ensure that every computational result has a precise interpretation and that no numerical observation is promoted to a theorem by software status or presentation.
