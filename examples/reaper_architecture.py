"""Runnable demonstration of the nine experimental Reaper runtime systems."""
from __future__ import annotations

from reaper.reaper_systems import (
    EpochArena,
    FFIPermissions,
    ForeignFunction,
    ForeignFunctionSpec,
    HotspotProfiler,
    IRModule,
    IRNode,
    RelayNetwork,
    SnapshotCodec,
    SovereignUnit,
    VanguardSentinel,
    effect_scope,
    require_effect,
    requires_effects,
)


# Citadel: local, typed routing without an intermediate serialization format.
relay = RelayNetwork()
relay.register("audit", lambda event: {"accepted": True, "event": event}, payload_type=dict)
print("relay:", relay.transmit("audit", {"kind": "boot"}))

# Harvest: promote the value that survives the epoch.
arena = EpochArena()
arena.allocate({"temporary": "discard"})
survivor = arena.promote(arena.allocate({"stable": 7}))
print("harvest:", arena.harvest().promoted, "survivor:", survivor)

# Effects: host capabilities are scoped and explicitly required.
@requires_effects("trace")
def traced(value: str) -> str:
    trace = require_effect("trace")
    return f"{trace}:{value}"

with effect_scope(trace="demo"):
    print("effect:", traced("ready"))

# Harbinger: profiling supports a backend-provided specialization.
profiler = HotspotProfiler(hot_threshold=2)
profiler.invoke("double", lambda value: value * 2, 4)
profiler.invoke("double", lambda value: value * 2, 5)
profiler.register_specialization("double", lambda value: value + value)
print("profiled:", profiler.invoke("double", lambda value: value * 2, 6))

# Synthesis: data and code-shaped nodes share one canonical representation.
ir = IRModule((IRNode("call", (IRNode("name", literal="sum"),)),))
print("IR SHA-256:", ir.digest)

# Dragon's Teeth: explicit, typed FFI adapter and exact-symbol permission.
negate = ForeignFunction(ForeignFunctionSpec("demo.negate", (int,), int), lambda value: -value)
with effect_scope(ffi=FFIPermissions({"demo.negate"})):
    print("FFI:", negate(5))

# Sovereign + Dark Space: bounded actor mailbox and authenticated hibernation.
def inventory_handler(state: dict[str, int], message: dict[str, int]):
    updated = {"count": state["count"] + message["delta"]}
    return updated, updated["count"]

unit = SovereignUnit("inventory", {"count": 0}, inventory_handler, mailbox_capacity=8)
unit.send({"delta": 3})
unit.drain()
secret = b"example-only-snapshot-secret"
snapshot = unit.hibernate(SnapshotCodec(), key=secret)
unit = SovereignUnit.awaken(snapshot, inventory_handler, key=secret, mailbox_capacity=8)
print("awakened actor:", unit.state)

# Vanguard: bounded, application-defined recovery callback.
healthy = {"value": False}
recovery_log: list[str] = []
sentinel = VanguardSentinel()
sentinel.watch("demo-service", lambda: healthy["value"], lambda: recovery_log.append("restart"), max_recoveries=1)
print("sentinel:", sentinel.inspect(), "recovery:", recovery_log)
