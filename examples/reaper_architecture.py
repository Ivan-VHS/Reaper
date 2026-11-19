"""Runnable overview of the nine Reaper architecture systems."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from reaper.checkpoint import SnapshotStore, TransactionalStore
from reaper.citadel import CitadelRouter
from reaper.compiler import compile_source, optimize
from reaper.concurrency import ActorSystem
from reaper.interop import parse_c_header
from reaper.profiling import RuntimeProfiler
from reaper.resources import EpochManager
from reaper.security import CapabilityAuthority, capability_scope, require_capability
from reaper.vanguard import VanguardSentinel


def run_actor_demo() -> tuple[list[int], tuple[dict[str, object], ...]]:
    async def run() -> tuple[list[int], tuple[dict[str, object], ...]]:
        handled: list[int] = []
        async with ActorSystem() as actors:
            worker = await actors.spawn(
                "counter",
                lambda: lambda value: handled.append(value),
                int,
                mailbox_capacity=8,
            )
            await worker.tell(7)
            await worker.tell(11)
            await worker.stop()
        return handled, actors.status()
    return asyncio.run(run())


# 1. Citadel — typed in-process routing; the payload is not serialized.
relay = CitadelRouter()
relay.register("audit", lambda event: {"accepted": True, "event": event}, payload_type=dict)
print("1 / Citadel:", relay.dispatch("audit", {"kind": "boot"}))

# 2. Harvest — logical region lifetimes and epoch-based handle invalidation.
epochs = EpochManager()
region = epochs.create_region("request", max_items=16)
reference = region.allocate({"request_id": 42})
print("2 / Harvest:", reference.read(), "reclaimed:", end=" ")
epochs.retire(region)
print(epochs.advance())

# 3. Indoctrination — explicit, revocable host capability scope.
authority = CapabilityAuthority(b"reaper-demo-secret-key-32-bytes!!")
token = authority.issue("trace.write", "demo")
with capability_scope(authority, token):
    print("3 / Effects:", require_capability("trace.write", "demo").capability)

# 4. Harbinger — measured hot-call counters; no generated machine code.
profiler = RuntimeProfiler()
print("4 / Profiler:", profiler.call("double", lambda value: value * 2, 21))
print("   hot sites:", profiler.hot_functions(minimum_calls=1))

# 5. Synthesis — static checking, source-mapped IR and constant folding.
compiled = compile_source("emit 20 + 22\n", strict=True)
optimized, stats = optimize(compiled)
print("5 / Synthesis:", optimized.ir_digest, "folded:", stats.folded_expressions)

# 6. Dragon's Teeth — parse only a deliberately small, scalar C declaration subset.
signatures = parse_c_header("int add(int left, int right);")
print("6 / FFI manifest:", signatures[0])

# 7. Dark Space — durable application-data snapshots, not live process checkpoints.
with tempfile.TemporaryDirectory() as temporary:
    store = SnapshotStore(Path(temporary) / "state.json")
    application = TransactionalStore(store, {"cycles": 0})
    with application.transaction() as state:
        state["cycles"] += 1
    print("7 / Snapshot:", application.get("cycles"))

# 8. Sovereign — bounded cooperative actors and structured shutdown.
handled, actor_status = run_actor_demo()
print("8 / Actors:", handled, actor_status)

# 9. Vanguard — explicit health inspection and bounded local recovery.
sentinel = VanguardSentinel()
sentinel.watch("actor-system", lambda: all(not item["failed"] for item in actor_status))
report = sentinel.inspect(actors=actor_status)
print("9 / Vanguard:", report.findings, "healthy:", report.healthy)
