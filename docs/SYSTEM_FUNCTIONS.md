# Reaper System Functions v1

The exported Reaper module is `stdlib/system.rpr`. Import it explicitly:

```rpr
import "../stdlib/system.rpr" as system

make report := system["contract_graph_check"](contracts)
emit report["ok"]
```

The module exposes ten system-function families. The functions are executable in
the current Python reference runtime through the ordinary Reaper `craft` API.
They are not yet implemented by the partial native C17 frontend/runtime.

| Requested capability | Reaper API | Current guarantee |
|---|---|---|
| Contract dependency graph | `contract_graph_check(contracts)` | Deterministic runtime preflight: unique IDs, missing references, cycles, and incompatible shared field declarations. The returned phase is `runtime_preflight`, not compiler `comptime`. |
| Bounded arena slot | `arena_slot(capacity_bytes, function)` | Executes a callback in a tracked region with a per-region tracked-allocation limit; copies out the callback result and rejects region escapes. Python host allocation is not a true zero-allocation arena. |
| Budgeted worker | `worker_budget(ms, bytes, function, args, state)` | Cooperative deadline checks at Reaper execution steps and a tracked-allocation region limit. Returns a bounded state snapshot and a halted/completed status. Not a process sandbox, hard CPU scheduler, or RSS cap; blocking host calls cannot be pre-empted. |
| Diff / reconcile | `diff_reconcile(before, after, key)`, `reconcile_apply(current, plan, invariant)` | Stable keyed upsert/drop/noop plan, target checksum, copy-on-apply, invariant validation, and checksum verification before returning a committed candidate. Caller-owned state is not mutated. |
| Ephemeral match | `ephemeral_match(left, right)` | Compares temporary SHA-256 digests and overwrites the function-owned mutable working buffers. It cannot erase the caller's original strings/bytes, copies made elsewhere, or immutable digest values. |
| Guarded mutation | `guarded_mutation(current, candidate, mode, validator, token)` | Automatic updates require a validator returning true. Manual overrides require an expiring, single-use `mutation:override` token issued by the embedding host through `OverrideAuthority.issue`; Reaper code cannot mint its own token. Revision metadata is retained in a bounded in-memory journal. |
| Lease window | `lease_window(start_ms, days, now_ms)` | Runtime calculation with explicit UTC epoch-millisecond inputs. The current type checker does not enforce type-level expiry. |
| Latency profiler | `latency_measure(label, function, args)`, `latency_report()` | In-memory per-label count/min/p95/p99/max measurements. No external agent, network export, or socket endpoint is started. |
| Local-only guard | `local_only_check(enabled, effects, imports)` | Explicit-effect/import preflight that rejects declared network-like capabilities. It is not yet a compiler-enforced module header; current runtime networking remains unavailable as an ambient builtin. |
| Migration and rollback | `rollback_plan_check(migration, rollback, fixtures)` | Runs forward and inverse functions on supplied fixtures and verifies restoration before deployment. This is a test/preflight function, not a type-level requirement on every contract version. |

Additional host API:

- `revision_log()` returns the bounded mutation audit journal.
- The embedding host creates override tokens with `OverrideAuthority.issue("mutation:override", ttl_ms)` and injects the token into the Reaper execution environment; no token-issuance builtin is registered for source code.
- `latency_reset()` clears local profiler samples.
- `reconcile_apply` is the only operation that constructs the reconciled candidate; it does not persist or publish it.

## Example

```rpr
import "../stdlib/system.rpr" as system

craft accept_snapshot(before, candidate) {
    yield size(candidate) <= 1000
}

make plan := system["diff_reconcile"](old_snapshot, new_snapshot, "id")
make checked := system["reconcile_apply"](old_snapshot, plan, accept_snapshot)
emit checked["committed"]

make local := system["local_only_check"](true, ["file.read"], ["reaper.core"])
emit local["ok"]
```

## Safety and implementation boundary

These APIs extend the Reaper reference runtime and are available to both its
tree-walk and bytecode-VM execution paths. The VM delegates host builtins to the
same reference implementation. This does not establish native C17 parity.

Three requested guarantees require future compiler/runtime work rather than a
wrapper function: genuine compile-time contract evaluation, type-level leases
and compile-time `local_only` enforcement. The worker currently provides
cooperative quotas, not OS-enforced isolation. The arena is a bounded tracked
region over the host allocator, not proof of zero host allocations. Arena callback
results must be finite JSON-compatible values that fit the slot byte budget.
Ephemeral comparison wipes only buffers owned by the function. These limits are explicit
so the API does not imply stronger guarantees than it provides.

## Verification

The integration suite exercises the Reaper API through both `treewalk` and
`vm`, including cycle rejection, bounded regions, cooperative worker halts,
reconciliation invariants/checksums, host-issued overrides, local-only checks,
latency percentiles and migration rollback fixtures.
