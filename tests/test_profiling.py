from __future__ import annotations

import unittest

from reaper.profiling import RuntimeProfiler


class ProfilerTests(unittest.TestCase):
    def test_calls_and_hotspot_thresholds_are_recorded(self) -> None:
        profiler = RuntimeProfiler()
        self.assertEqual(profiler.call("double", lambda value: value * 2, 4), 8)
        profiler.record_call("loop", count=3)
        report = {item.name: item for item in profiler.report()}
        self.assertEqual(report["double"].calls, 1)
        self.assertGreaterEqual(report["double"].total_ns, 0)
        self.assertEqual(profiler.hot_functions(minimum_calls=2), ("loop",))

    def test_measure_records_even_when_body_fails(self) -> None:
        profiler = RuntimeProfiler()
        with self.assertRaises(ValueError):
            with profiler.measure("failure"):
                raise ValueError("expected")
        self.assertEqual(profiler.report()[0].calls, 1)


if __name__ == "__main__":
    unittest.main()
