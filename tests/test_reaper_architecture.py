from __future__ import annotations

import unittest

from reaper.actors import ActorError, ActorHibernatedError, SovereignUnit
from reaper.effects import EffectUnavailableError, current_effects, effect_scope, get_effect
from reaper.epoch import EpochArena, EpochCapacityError, EpochClosedError, EpochError
from reaper.profiling import HotPathProfiler
from reaper.relays import RelayBus, RelayError, UnknownRelayError
from reaper.sentinel import HealthSample, SentinelPolicy, VanguardSentinel


class EpochArenaTests(unittest.TestCase):
    def test_harvest_releases_references_and_advances_generation(self) -> None:
        arena = EpochArena(max_objects=2)
        first, second = object(), object()
        arena.allocate(first)
        arena.allocate(second)
        self.assertEqual(arena.harvest(), 2)
        self.assertEqual(arena.active_objects, 0)
        self.assertEqual(arena.generation, 1)

    def test_capacity_and_closed_state_are_enforced(self) -> None:
        arena = EpochArena(max_objects=1)
        arena.retain("one")
        with self.assertRaises(EpochCapacityError):
            arena.retain("two")
        arena.close()
        with self.assertRaises(EpochClosedError):
            arena.retain("three")

    def test_promotion_moves_reference_to_parent(self) -> None:
        root = EpochArena[object]()
        child = EpochArena(parent=root)
        value = object()
        child.retain(value)
        self.assertIs(child.promote(value), value)
        self.assertEqual(child.active_objects, 0)
        self.assertEqual(root.active_objects, 1)

    def test_promotion_requires_parent_and_membership(self) -> None:
        with self.assertRaises(EpochError):
            EpochArena().promote(object())


class EffectContextTests(unittest.TestCase):
    def test_nested_effects_shadow_then_restore(self) -> None:
        self.assertEqual(dict(current_effects()), {})
        with effect_scope(trace_id="outer", db="primary"):
            self.assertEqual(get_effect("trace_id"), "outer")
            with effect_scope(trace_id="inner"):
                self.assertEqual(get_effect("trace_id"), "inner")
                self.assertEqual(get_effect("db"), "primary")
            self.assertEqual(get_effect("trace_id"), "outer")
        self.assertEqual(dict(current_effects()), {})

    def test_missing_effect_has_a_specific_error(self) -> None:
        with self.assertRaises(EffectUnavailableError):
            get_effect("transaction")

    def test_effect_view_is_immutable(self) -> None:
        with effect_scope(clock="test") as active:
            with self.assertRaises(TypeError):
                active["clock"] = "changed"


class RelayBusTests(unittest.TestCase):
    def test_typed_local_delivery(self) -> None:
        bus = RelayBus()
        bus.register("metrics.ingest", lambda value: value + 1, payload_type=int)
        self.assertEqual(bus.send("metrics.ingest", 41), 42)

    def test_rejects_wrong_payload_and_duplicate_endpoint(self) -> None:
        bus = RelayBus()
        bus.register("jobs", lambda value: value, payload_type=dict)
        with self.assertRaises(TypeError):
            bus.send("jobs", "not-a-dict")
        with self.assertRaises(RelayError):
            bus.register("jobs", lambda value: value)

    def test_unknown_endpoint_is_reported(self) -> None:
        with self.assertRaises(UnknownRelayError):
            RelayBus().send("missing", None)


class SovereignUnitTests(unittest.TestCase):
    @staticmethod
    def add(state, message):
        return {"total": state["total"] + message["amount"]}

    def test_fifo_drain_and_snapshot_restore(self) -> None:
        actor = SovereignUnit("ledger", {"total": 1}, self.add)
        actor.send({"amount": 2})
        actor.send({"amount": 3})
        self.assertEqual(actor.drain(max_messages=1), 1)
        snapshot = actor.hibernate()
        self.assertTrue(actor.hibernated)
        with self.assertRaises(ActorHibernatedError):
            actor.send({"amount": 4})
        restored = SovereignUnit("ledger", {"total": 0}, self.add)
        # Wake is a lifecycle transition on the actor that produced the snapshot.
        actor.wake(snapshot)
        self.assertEqual(actor.state, {"total": 3})
        self.assertEqual(actor.mailbox_size, 1)
        actor.drain()
        self.assertEqual(actor.state, {"total": 6})
        self.assertEqual(restored.state, {"total": 0})

    def test_handler_failure_does_not_commit_state_or_remove_message(self) -> None:
        def fail(_state, _message):
            raise RuntimeError("boom")
        actor = SovereignUnit("failing", {"value": 1}, fail)
        actor.send("message")
        with self.assertRaises(RuntimeError):
            actor.drain()
        self.assertEqual(actor.state, {"value": 1})
        self.assertEqual(actor.mailbox_size, 1)

    def test_snapshot_integrity_and_identity_are_checked(self) -> None:
        actor = SovereignUnit("a", {"value": 1}, self.add)
        snapshot = actor.hibernate()
        altered = snapshot.replace(b'"value":1', b'"value":2')
        with self.assertRaises(ActorError):
            actor.wake(altered)
        other = SovereignUnit("b", {"value": 0}, self.add)
        other.hibernate()
        with self.assertRaises(ActorError):
            other.wake(snapshot)

    def test_actor_state_must_be_json_compatible(self) -> None:
        with self.assertRaises(ValueError):
            SovereignUnit("bad", object(), self.add)

    def test_snapshot_rejects_non_object_payload(self) -> None:
        actor = SovereignUnit("malformed", {"value": 1}, self.add)
        actor.hibernate()
        with self.assertRaises(ActorError):
            actor.wake(b'{"payload":[],"sha256":"not-a-digest"}')


class ProfilingAndSentinelTests(unittest.TestCase):
    def test_hot_paths_are_ranked_after_threshold(self) -> None:
        profiler = HotPathProfiler(hot_threshold=3)
        profiler.record("parse", 2)
        profiler.record("evaluate", 3)
        profiler.record("parse", 2)
        self.assertEqual(
            [(item.name, item.calls) for item in profiler.candidates()],
            [("parse", 4), ("evaluate", 3)],
        )

    def test_sentinel_escalates_only_after_sustained_critical_samples(self) -> None:
        sentinel = VanguardSentinel(SentinelPolicy(sustained_critical_samples=2))
        first = sentinel.observe(HealthSample(0.99, 0.4, 0.0, 10.0))
        second = sentinel.observe(HealthSample(0.99, 0.4, 0.0, 10.0))
        self.assertEqual(first.action, "investigate")
        self.assertEqual(second.action, "review-restart-or-scale")
        self.assertEqual(second.severity, "critical")

    def test_sentinel_rejects_invalid_metrics(self) -> None:
        sentinel = VanguardSentinel()
        with self.assertRaises(ValueError):
            sentinel.observe(HealthSample(1.5, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
