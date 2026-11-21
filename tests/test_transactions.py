from __future__ import annotations

import asyncio
import unittest

from reaper.transactions import (
    RuntimeTransaction,
    TransactionConflict,
    TransactionError,
    TransactionLimitError,
)


class RuntimeTransactionTests(unittest.TestCase):
    def test_patch_remap_rebind_and_commit(self) -> None:
        events: list[tuple[str, int]] = []
        tx = RuntimeTransaction({"sensor": {"lambda": 1.0}, "mode": "safe"}, event_sink=lambda n, g: events.append((n, g)))
        tx.patch(("sensor", "lambda"), 0.98).rebind("binding", "bank1")
        tx.remap({"mode": "profile"})
        snapshot = tx.flash(expected_generation=0)
        self.assertEqual(snapshot.generation, 1)
        self.assertEqual(snapshot.payload["sensor"]["lambda"], 0.98)
        self.assertEqual(snapshot.payload["profile"], "safe")
        self.assertEqual(snapshot.payload["binding"], "bank1")
        self.assertTrue(tx.validate())
        self.assertIn(("FLASH_COMMITTED", 1), events)

    def test_stale_commit_conflicts_and_rollback_restores(self) -> None:
        tx = RuntimeTransaction({"version": 1})
        tx.patch(("version",), 2)
        tx.flash(0)
        tx.patch(("version",), 3)
        with self.assertRaises(TransactionConflict):
            tx.flash(0)
        restored = tx.rollback()
        self.assertEqual(restored.payload, {"version": 2})

    def test_hot_swap_and_monotonic_migration(self) -> None:
        tx = RuntimeTransaction({"schema": 1, "items": [1, 2]})
        tx.hot_swap({"schema": 1, "items": [3, 4]})
        tx.migrate(2, lambda state: {**state, "schema": 2, "checksum_ready": True})
        result = tx.reflash()
        self.assertEqual(result.schema_version, 2)
        self.assertTrue(result.payload["checksum_ready"])
        with self.assertRaises(TransactionError):
            tx.migrate(2, lambda state: state)

    def test_bounds_and_invalid_remap_are_rejected(self) -> None:
        tx = RuntimeTransaction({"a": "abc"}, max_bytes=32)
        with self.assertRaises(TransactionLimitError):
            tx.hot_swap({"a": "x" * 100})
        with self.assertRaises(TransactionError):
            tx.remap({"missing": "new"})
        with self.assertRaises(TransactionError):
            tx.patch(("a", 9), "bad")

    def test_control_flow_helpers_and_guarded_panic(self) -> None:
        self.assertEqual(RuntimeTransaction.return_value(7), 7)
        tx = RuntimeTransaction({"checkpoint": 1})
        self.assertEqual(tx.yield_value("safe"), "safe")
        _, error = RuntimeTransaction.catch(RuntimeTransaction.throw, "recoverable")
        self.assertEqual(error, "recoverable")
        with self.assertRaises(TransactionError):
            RuntimeTransaction.assert_condition(False, "limit exceeded")
        tx = RuntimeTransaction({"safe": True})
        with self.assertRaisesRegex(TransactionError, "panic"):
            tx.panic("guarded failure")
        tx.rollback()

    def test_async_await_and_sync(self) -> None:
        async def run() -> None:
            tx = RuntimeTransaction({"ready": False})
            tx.patch(("ready",), True)
            result = await RuntimeTransaction.await_result(asyncio.create_task(tx.async_flash(0)))
            self.assertTrue(result.payload["ready"])
            tx.patch(("ready",), False)
            self.assertFalse(tx.sync().payload["ready"])
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
