from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from reaper.cli import main
from reaper.reaper_systems import (
    ARCHITECTURE_FEATURES,
    ArchitectureError,
    CapabilityError,
    EpochArena,
    FFIPermissions,
    ForeignFunction,
    ForeignFunctionSpec,
    HotspotProfiler,
    IRModule,
    IRNode,
    MailboxFull,
    MissingEffectError,
    ProfileTier,
    RelayNetwork,
    SnapshotCodec,
    SovereignUnit,
    VanguardSentinel,
    architecture_summary,
    effect_scope,
    require_effect,
    requires_effects,
)


class CitadelRelayTests(unittest.TestCase):
    def test_route_passes_the_original_object_without_serializing(self) -> None:
        relay = RelayNetwork()
        payload = {"sequence": [1, 2, 3]}
        relay.register("worker", lambda value: value)
        self.assertIs(relay.transmit("worker", payload), payload)

    def test_typed_routes_reject_mismatched_payloads(self) -> None:
        relay = RelayNetwork()
        relay.register("numbers", lambda value: value * 2, payload_type=int)
        self.assertEqual(relay.transmit("numbers", 21), 42)
        with self.assertRaises(TypeError):
            relay.transmit("numbers", "21")

    def test_duplicate_and_missing_routes_are_errors(self) -> None:
        relay = RelayNetwork()
        relay.register("one", lambda value: value)
        with self.assertRaises(ArchitectureError):
            relay.register("one", lambda value: value)
        with self.assertRaises(ArchitectureError):
            relay.transmit("missing", None)
        self.assertTrue(relay.unregister("one"))
        self.assertFalse(relay.unregister("one"))


class EpochHarvestTests(unittest.TestCase):
    def test_harvest_releases_temporary_values_and_promotes_selected_values(self) -> None:
        arena = EpochArena()
        temporary = arena.allocate({"temporary": True})
        persistent = arena.allocate({"persistent": True})
        self.assertIs(arena.promote(persistent), persistent)
        report = arena.harvest()
        self.assertEqual(report.generation, 0)
        self.assertEqual(report.allocation_count, 2)
        self.assertEqual(report.reclaimed_count, 1)
        self.assertEqual(report.promoted, (persistent,))
        self.assertEqual(arena.generation, 1)
        self.assertEqual(temporary, {"temporary": True})

    def test_cannot_promote_a_value_from_another_epoch(self) -> None:
        with self.assertRaises(ArchitectureError):
            EpochArena().promote(object())

    def test_context_manager_harvests_even_when_body_raises(self) -> None:
        arena = EpochArena()
        with self.assertRaisesRegex(RuntimeError, "boom"):
            with arena:
                arena.allocate("short lived")
                raise RuntimeError("boom")
        self.assertIsNotNone(arena.last_report)
        self.assertEqual(arena.last_report.reclaimed_count, 1)


class EffectScopeTests(unittest.TestCase):
    def test_effects_are_required_and_scoped(self) -> None:
        with self.assertRaises(MissingEffectError):
            require_effect("database")
        with effect_scope(database="transaction-42"):
            self.assertEqual(require_effect("database"), "transaction-42")
            with effect_scope(trace="trace-7"):
                self.assertEqual(require_effect("database"), "transaction-42")
                self.assertEqual(require_effect("trace"), "trace-7")
            with self.assertRaises(MissingEffectError):
                require_effect("trace")
        with self.assertRaises(MissingEffectError):
            require_effect("database")

    def test_required_effect_decorator_fails_closed(self) -> None:
        @requires_effects("transaction", "trace")
        def operation(value: int) -> int:
            return value + 1

        with self.assertRaises(MissingEffectError):
            operation(4)
        with effect_scope(transaction=object(), trace=object()):
            self.assertEqual(operation(4), 5)


class HarbingerProfilerTests(unittest.TestCase):
    def test_hot_calls_can_register_an_explicit_specialization(self) -> None:
        profiler = HotspotProfiler(hot_threshold=2)
        profiler.record("square", 10)
        self.assertEqual(profiler.snapshot("square").tier, ProfileTier.COLD)
        profiler.record("square", 20)
        self.assertEqual(profiler.snapshot("square").tier, ProfileTier.HOT)
        with self.assertRaises(ArchitectureError):
            profiler.register_specialization("not-seen", lambda value: value)
        profiler.register_specialization("square", lambda value: value * value + 1)
        self.assertEqual(profiler.invoke("square", lambda value: value * value, 3), 10)
        snapshot = profiler.snapshot("square")
        self.assertEqual(snapshot.tier, ProfileTier.SPECIALIZED)
        self.assertEqual(snapshot.calls, 3)

    def test_invoke_records_duration_when_target_raises(self) -> None:
        profiler = HotspotProfiler(hot_threshold=1)

        def broken() -> None:
            raise ValueError("expected")

        with self.assertRaises(ValueError):
            profiler.invoke("broken", broken)
        self.assertEqual(profiler.snapshot("broken").calls, 1)

    def test_threshold_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            HotspotProfiler(0)


class SemanticIRTests(unittest.TestCase):
    def test_canonical_ir_is_stable_across_attribute_order(self) -> None:
        left = IRModule((IRNode("call", (IRNode("name", literal="sum"),), attributes=(("z", 2), ("a", 1))),))
        right = IRModule((IRNode("call", (IRNode("name", literal="sum"),), attributes=(("a", 1), ("z", 2))),))
        self.assertTrue(left.equivalent_to(right))
        self.assertEqual(left.digest, right.digest)
        self.assertEqual(len(left.digest), 64)

    def test_semantic_change_changes_digest(self) -> None:
        first = IRModule((IRNode("literal", literal=1),))
        second = IRModule((IRNode("literal", literal=2),))
        self.assertNotEqual(first.digest, second.digest)
        self.assertFalse(first.equivalent_to(second))

    def test_ir_rejects_invalid_values_and_duplicate_attributes(self) -> None:
        with self.assertRaises(ValueError):
            IRNode("literal", attributes=(("x", 1), ("x", 2)))
        with self.assertRaises(TypeError):
            IRNode("literal", literal=[1, 2])  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            IRNode("call", children=(object(),))  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            IRModule((object(),))  # type: ignore[arg-type]


class GuardedFFITests(unittest.TestCase):
    def setUp(self) -> None:
        self.sqrt = ForeignFunction(
            ForeignFunctionSpec("math.sqrt", (float,), float),
            lambda value: value ** 0.5,
        )

    def test_ffi_requires_explicit_symbol_permission(self) -> None:
        with self.assertRaises(MissingEffectError):
            self.sqrt(9.0)
        with effect_scope(ffi=FFIPermissions({"math.floor"})):
            with self.assertRaises(CapabilityError):
                self.sqrt(9.0)
        with effect_scope(ffi=FFIPermissions({"math.sqrt"})):
            self.assertEqual(self.sqrt(9.0), 3.0)

    def test_ffi_validates_argument_and_result_types(self) -> None:
        with effect_scope(ffi=FFIPermissions({"math.sqrt"})):
            with self.assertRaises(TypeError):
                self.sqrt(True)
        broken = ForeignFunction(
            ForeignFunctionSpec("broken", (), int),
            lambda: "not an integer",
        )
        with effect_scope(ffi=FFIPermissions({"broken"})):
            with self.assertRaises(TypeError):
                broken()


class SnapshotTests(unittest.TestCase):
    def test_unsigned_snapshot_round_trip_and_integrity(self) -> None:
        codec = SnapshotCodec()
        snapshot = codec.freeze({"count": 4, "items": ["a", "b"]})
        self.assertEqual(codec.restore(snapshot), {"count": 4, "items": ["a", "b"]})
        tampered = type(snapshot)(snapshot.codec_version, snapshot.payload + b" ", snapshot.digest, snapshot.mac)
        with self.assertRaisesRegex(ArchitectureError, "integrity"):
            codec.restore(tampered)

    def test_authenticated_snapshot_requires_the_correct_key(self) -> None:
        codec = SnapshotCodec()
        key = b"a sufficiently long secret key"
        snapshot = codec.freeze({"ready": True}, key=key)
        with self.assertRaises(CapabilityError):
            codec.restore(snapshot)
        with self.assertRaises(CapabilityError):
            codec.restore(snapshot, key=b"another sufficiently long key")
        self.assertEqual(codec.restore(snapshot, key=key), {"ready": True})

    def test_snapshot_size_and_value_limits(self) -> None:
        with self.assertRaises(ArchitectureError):
            SnapshotCodec(max_bytes=3).freeze({"long": "value"})
        with self.assertRaises(TypeError):
            SnapshotCodec().freeze({1: "non-text map key"})
        with self.assertRaises(ValueError):
            SnapshotCodec().freeze(float("nan"))


class SovereignUnitTests(unittest.TestCase):
    @staticmethod
    def handler(state: dict[str, int], message: dict[str, int]) -> tuple[dict[str, int], int]:
        new_count = state["count"] + message["amount"]
        return {"count": new_count}, new_count

    def test_actor_processes_messages_in_fifo_order(self) -> None:
        unit = SovereignUnit("ledger-a", {"count": 0}, self.handler, mailbox_capacity=2)
        unit.send({"amount": 2})
        unit.send({"amount": 3})
        self.assertEqual(unit.drain(), [2, 5])
        self.assertEqual(unit.state, {"count": 5})
        self.assertEqual(unit.processed_count, 2)

    def test_mailbox_is_bounded(self) -> None:
        unit = SovereignUnit("ledger-b", {"count": 0}, self.handler, mailbox_capacity=1)
        unit.send({"amount": 1})
        with self.assertRaises(MailboxFull):
            unit.send({"amount": 2})

    def test_failed_handler_preserves_state_and_consumes_failed_message(self) -> None:
        def broken(state: dict[str, int], message: object) -> tuple[dict[str, int], None]:
            raise RuntimeError("handler failed")

        unit = SovereignUnit("ledger-c", {"count": 7}, broken)
        unit.send({"amount": 9})
        with self.assertRaisesRegex(RuntimeError, "handler failed"):
            unit.process_one()
        self.assertEqual(unit.state, {"count": 7})
        self.assertEqual(unit.mailbox_size, 0)

    def test_hibernate_and_awaken_preserves_state_and_mailbox(self) -> None:
        unit = SovereignUnit("ledger-d", {"count": 4}, self.handler, mailbox_capacity=4)
        unit.send({"amount": 6})
        key = b"snapshot authentication secret"
        snapshot = unit.hibernate(key=key)
        self.assertTrue(unit.is_hibernated)
        with self.assertRaises(ArchitectureError):
            unit.send({"amount": 1})
        awakened = SovereignUnit.awaken(snapshot, self.handler, key=key, mailbox_capacity=4)
        self.assertEqual(awakened.state, {"count": 4})
        self.assertEqual(awakened.drain(), [10])
        self.assertEqual(awakened.state, {"count": 10})

    def test_actor_state_and_messages_must_be_json_data(self) -> None:
        with self.assertRaises(TypeError):
            SovereignUnit("bad", object(), self.handler)
        unit = SovereignUnit("good", {"count": 0}, self.handler)
        with self.assertRaises(TypeError):
            unit.send(object())


class VanguardSentinelTests(unittest.TestCase):
    def test_failed_probe_invokes_recovery_only_within_budget(self) -> None:
        recovered: list[str] = []
        sentinel = VanguardSentinel()
        sentinel.watch("api", lambda: False, lambda: recovered.append("restart"), max_recoveries=1)
        first = sentinel.inspect()[0]
        second = sentinel.inspect()[0]
        self.assertFalse(first.healthy)
        self.assertTrue(first.recovered)
        self.assertFalse(second.recovered)
        self.assertEqual(recovered, ["restart"])

    def test_probe_exception_is_reported_and_recovery_runs(self) -> None:
        sentinel = VanguardSentinel()
        sentinel.watch("db", lambda: (_ for _ in ()).throw(OSError("offline")), lambda: None)
        report = sentinel.inspect()[0]
        self.assertFalse(report.healthy)
        self.assertTrue(report.recovered)
        self.assertIn("offline", report.detail)

    def test_healthy_probe_does_not_recover(self) -> None:
        calls: list[bool] = []
        sentinel = VanguardSentinel()
        sentinel.watch("worker", lambda: True, lambda: calls.append(True))
        self.assertTrue(sentinel.inspect()[0].healthy)
        self.assertEqual(calls, [])


class ArchitectureCatalogueTests(unittest.TestCase):
    def test_all_nine_systems_are_registered_with_boundaries(self) -> None:
        self.assertEqual([item.id for item in ARCHITECTURE_FEATURES], list(range(1, 10)))
        self.assertTrue(all(item.name and item.implementation and item.boundary for item in ARCHITECTURE_FEATURES))
        summary = architecture_summary()
        self.assertIn("Citadel Relays", summary)
        self.assertIn("Vanguard Sentinel", summary)

    def test_cli_exposes_the_architecture_catalogue(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--architecture"]), 0)
        self.assertIn("Citadel Relays", output.getvalue())
        self.assertIn("Vanguard Sentinel", output.getvalue())


if __name__ == "__main__":
    unittest.main()
