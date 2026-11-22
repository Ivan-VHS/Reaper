# Transactional Runtime Contract v1

Reaper's host/runtime API is available from `reaper.transactions` and is re-exported from `reaper`.

```python
from reaper import RuntimeTransaction

tx = RuntimeTransaction({"profile": "safe", "limits": {"steps": 1000}})
tx.patch(("limits", "steps"), 1500)
tx.rebind("sensor.bank1", {"source": "observed"})
tx.remap({"profile": "active_profile"})
snapshot = tx.flash(expected_generation=0)
```

## Operation map

| Operation | API | Meaning |
|---|---|---|
| `patch` | `tx.patch(path, value)` | Stage a nested mapping/list change |
| `rebind` | `tx.rebind(name, value)` | Bind a named value in root mapping state |
| `remap` | `tx.remap({old: new})` | Rename mapping keys with collision checks |
| `hotSwap` | `tx.hot_swap(value)` | Replace the staged in-memory state |
| `migrate` | `tx.migrate(schema, transform)` | Apply a monotonic schema migration |
| `flash` / `reflash` | `tx.flash()`, `tx.reflash()` | Commit with optimistic generation checking |
| `rollback` | `tx.rollback()` | Restore last committed payload and schema |
| `sync` | `tx.sync()` | Commit against the current generation |
| `async` / `await` | `await tx.async_flash()` | Run commit off the event loop and await its snapshot |
| `emit` / `yield` | `tx.emit(name)`, `tx.yield_value(value)` | Emit an event or checkpoint |
| `throw` / `catch` | `tx.throw(message)`, `RuntimeTransaction.catch(fn)` | Raise/capture a transaction error |
| `panic` / `assert` | `tx.panic(message)`, `RuntimeTransaction.assert_condition(...)` | Record a guarded failure or enforce an invariant |
| `return` | `RuntimeTransaction.return_value(value)` | Pass a value through |

## Safety properties

State must be finite JSON-compatible data. Default maximum canonical payload size is 4 MiB. Each committed snapshot has a SHA-256 digest and monotonically increasing generation. A stale generation raises `TransactionConflict`; migration versions must increase. A guarded panic poisons the transaction until rollback.

This is a host API over caller-owned in-memory state. It does not add physical firmware flashing, unrestricted code loading, or operating-system mutation to the Reaper language runtime.

## Tests

Run `python -m unittest tests.test_transactions -v` from the repository root.
