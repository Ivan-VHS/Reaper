# Scalar medium and deterministic stack synthesis

**Status:** executable Reaper reference-runtime module; native AOT parity is not yet implemented.

This feature turns the scalar-environment and technology-fusion concepts into bounded algorithms with explicit data contracts. The physical vocabulary is explanatory only: the implementation uses integer fields, graph edges, Q16 ratios and checked resource estimates.

## 1. Scalar medium

The v1 `ScalarMedium` record is represented by a validated four-element Reaper list:

`[potential_u64, density_u64, binding_energy_u64, half_life_ticks_u32]`

The reference implementation provides:

- `scalar_field_step(field, relaxation_q16, elapsed_ticks)`: scalar relaxation over a cyclic one-dimensional topology. Each cell moves toward the integer mean of its two neighbours using a Q16 interpolation factor in the range 0..65536.
- `decay_by_completed_half_lives`: potential is halved once per completed half-life interval. This is a deterministic tick-quantized rule, not a continuous exponential solver.
- `scalar_field_gradient(field)`: maximum absolute difference between adjacent scalar potentials. It reports magnitude only; no directional vector is inferred.
- `scalar_field_flux(field, quantum_step)`: multiplies the available potential above the threshold by each cell's density, then adds its binding-energy field, with multiplication and accumulation overflow checks.

The ring is an explicit v1 topology chosen to make boundary behavior deterministic. A general adjacency-list graph, multidimensional grids and vector/tensor fields are future extensions. Density and binding energy remain scalar state fields; the current relaxation pass updates potential only.

## 2. Stack fusion plan

The v1 `StackModule` descriptor is:

`[id_u64, contract_key, abi_major_u32, local_only, deprecated, private_bytes_u64, shared_runtime_key_u64, shared_bytes_u64, compute_units_u64]`

A dependency edge is:

`[consumer_id, provider_id, required_contract_key, required_abi_major]`

A policy is:

`[memory_budget_bytes, compute_budget_units, require_local_only, allow_deprecated]`

`stack_synthesize` performs bounded validation (64 modules and 256 edges), rejects duplicate IDs, missing/self dependencies, contract/ABI mismatch, incompatible shared-runtime keys, disallowed remote or deprecated modules, arithmetic overflow and budget violations. It then generates a stable topological order: among all currently ready modules, it chooses the smallest numeric ID. Input ordering therefore does not affect the plan.

The plan reports:

`["ok", ordered_ids, independent_bytes, fused_bytes, shared_bytes_eliminated, compute_units]`

The memory estimate deduplicates only explicitly declared shared-runtime groups. The shared key, ABI major and byte footprint must agree. `shared_bytes_eliminated` is an estimate derived from these descriptors; it is not a measured reduction in linked executable size, resident memory or latency. The output is an integration plan, not an automatic source merge or repository mutation.

## 3. Criticality governor

`assess_criticality(sample, minimum_q16, maximum_q16)` consumes:

`[accepted_tasks, spawned_tasks, queue_depth, queue_capacity, active_workers, worker_slots]`

It computes:

`k_eff_q16 = spawned_tasks * 65536 / accepted_tasks`

using integer arithmetic and checks scaling overflow. The plan is stable only when `k_eff <= 1`, the queue is below capacity, and active workers do not exceed worker slots. The separate `balanced` flag indicates whether the measured ratio falls inside the policy's Q16 window (the sample uses 0.90..1.00).

This is a counter-based admission/stability gate. It does not create threads, schedule work or claim control over an external queue.

## 4. What “neuroautomatic synthesis” means here

The v1 planner is deterministic and policy-driven. It validates contracts, scores no opaque learned model, and produces the same plan for the same descriptors and edges. “Neuroautomatic” is a design metaphor for adaptive planning, not a claim that a neural network is trained or that the compiler autonomously rewrites arbitrary foreign code.

A future candidate-selector can add measured cost vectors (startup time, memory, throughput, energy, ABI compatibility) and select among providers, but only where the selection evidence and contract are explicit.

## 5. Language and runtime boundary

The current frontend does not implement the sample's `contract`, `comptime`, `budget` or `arena_slot` syntax. This module instead uses ordinary Reaper `craft`, `make`, `vary`, `each`, `when`, `loop`, list and assertion constructs. Its tests execute the Reaper source on the reference runtime.

The existing native C17 AOT backend supports a much smaller scalar subset and does not yet compile this list-and-loop module. No claim of native AOT parity, compile-time evaluation or automatic foreign-language fusion is made.

The module is local and pure: it reads caller-supplied descriptors and counters, performs bounded computations, and returns results. It performs no filesystem, network, process, driver, shell or repository operations.
