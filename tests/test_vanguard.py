from __future__ import annotations

import unittest

from reaper.vanguard import VanguardSentinel


class VanguardSentinelTests(unittest.TestCase):
    def test_healthy_probe_and_actor_status(self) -> None:
        sentinel = VanguardSentinel()
        sentinel.watch("database", lambda: True)
        report = sentinel.inspect(actors=({"name": "worker", "failed": False, "done": False},))
        self.assertTrue(report.healthy)
        self.assertEqual([item.state for item in report.findings], ["healthy", "healthy"])

    def test_unhealthy_probe_is_reported_and_recovery_is_explicit(self) -> None:
        recovered: list[str] = []
        sentinel = VanguardSentinel()
        sentinel.watch("cache", lambda: False, lambda: recovered.append("reset"), max_recoveries=1)
        report = sentinel.inspect()
        self.assertFalse(report.healthy)
        self.assertEqual(len(report.unhealthy), 1)
        self.assertEqual(recovered, [])
        self.assertTrue(sentinel.recover("cache"))
        self.assertEqual(recovered, ["reset"])
        self.assertFalse(sentinel.recover("cache"))

    def test_probe_exception_and_actor_failure_are_critical(self) -> None:
        sentinel = VanguardSentinel()
        def broken():
            raise OSError("probe unavailable")
        sentinel.watch("disk", broken)
        report = sentinel.inspect(actors=({
            "name": "worker", "failed": True, "failure": "handler crashed",
        },))
        self.assertEqual([item.state for item in report.findings], ["critical", "critical"])
        self.assertIn("OSError", report.findings[0].detail)

    def test_restart_history_marks_actor_degraded(self) -> None:
        sentinel = VanguardSentinel()
        report = sentinel.inspect(actors=({
            "name": "worker", "failed": False, "restarts": 2, "done": False,
        },))
        self.assertEqual(report.findings[0].state, "degraded")

    def test_recovery_budget_and_watch_limits_are_enforced(self) -> None:
        sentinel = VanguardSentinel(max_watches=1)
        sentinel.watch("one", lambda: False, lambda: None, max_recoveries=1)
        with self.assertRaises(ValueError):
            sentinel.watch("two", lambda: True)
        sentinel.inspect()
        self.assertTrue(sentinel.recover("one"))
        self.assertFalse(sentinel.recover("one"))
        with self.assertRaises(ValueError):
            sentinel.watch("invalid", lambda: True, max_recoveries=1)


if __name__ == "__main__":
    unittest.main()
