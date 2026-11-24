from __future__ import annotations

import unittest

from reaper.errors import ReaperRuntimeError
from reaper.runtime import Interpreter
from reaper.streaming import ResultValue, StreamValue


class StreamingRuntimeTests(unittest.TestCase):
    def run_source(self, source: str, **options: object) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, **options).run(source)
        return output

    def test_stream_map_filter_fold_runs_as_one_fused_pipeline(self) -> None:
        output = self.run_source(
            """
craft double(value) {
    yield value * 2
}
craft above_three(value) {
    yield value > 3
}
craft add(accumulator, value) {
    yield accumulator + value
}
make total := [1, 2, 3, 4] :: stream() :: map(double) :: filter(above_three) :: fold(0, add)
emit total
"""
        )
        self.assertEqual(output, ["18"])

    def test_stream_views_share_single_use_source_and_append_stages(self) -> None:
        source = StreamValue(iter([1, 2, 3]), max_items=3)
        mapped = source.map(lambda value: value * 2)
        filtered = mapped.filter(lambda value: value > 2)

        self.assertIs(source._state, mapped._state)
        self.assertIs(mapped._state, filtered._state)
        self.assertEqual(filtered.stage_count, 2)
        self.assertEqual(list(filtered.iter_fused()), [4, 6])
        self.assertTrue(source.consumed)
        with self.assertRaisesRegex(ValueError, "closed|consumed"):
            list(source.iter_fused())

    def test_stream_enforces_item_limit_for_unknown_length_sources(self) -> None:
        source = StreamValue(iter([1, 2, 3]), max_items=2)
        with self.assertRaisesRegex(ValueError, "stream item limit"):
            list(source.iter_fused())

    def test_result_composition_and_error_mapping(self) -> None:
        output = self.run_source(
            """
craft sum_values(values) {
    yield values[0] + values[1] + values[2]
}
craft explain(message) {
    yield "parse-error: " ++ message
}
make good := zip3_ok(try_int("4"), try_int("5"), try_float("6.0")) :: map_ok(sum_values)
make bad := try_int("not-a-number") :: map_err(explain)
emit result_is_ok(good)
emit result_value(good)
emit result_is_err(bad)
emit result_error(bad)
"""
        )
        self.assertEqual(output[0:3], ["true", "15.0", "true"])
        self.assertEqual(output[3], "parse-error: expected ASCII decimal digits")

    def test_zip3_ok_preserves_first_error_without_calling_success_mapper(self) -> None:
        result = ResultValue.err("first failure")
        output = self.run_source(
            """
craft should_not_run(values) {
    assert(false, "mapper must not run for Err")
    yield values
}
make combined := zip3_ok(ok(1), err("first failure"), ok(3)) :: map_ok(should_not_run)
emit result_is_err(combined)
emit result_error(combined)
"""
        )
        self.assertEqual(output, ["true", "first failure"])
        self.assertTrue(result.is_err)

    def test_split_limit_preserves_the_unparsed_message_tail(self) -> None:
        output = self.run_source(
            """
make fields := split_limit("2026-11-24T02:45:00Z | auth | 503 | 18.4 | gateway | timeout", " | ", 4)
emit size(fields)
emit fields[4]
"""
        )
        self.assertEqual(output, ["5", "gateway | timeout"])

    def test_strict_numeric_and_rfc3339_parsers(self) -> None:
        output = self.run_source(
            """
make integer := try_int("503")
make decimal := try_float("18.4")
make invalid_decimal := try_float("NaN")
make timestamp := try_rfc3339("2026-11-24T02:45:00Z")
make invalid_timestamp := try_rfc3339("2026-02-30T02:45:00Z")
emit result_value(integer)
emit result_value(decimal)
emit result_is_err(invalid_decimal)
emit kind(result_value(timestamp))
emit result_is_err(invalid_timestamp)
"""
        )
        self.assertEqual(output, ["503", "18.4", "true", "datetime", "true"])

    def test_map_alter_is_atomic_and_analysis_has_standard_empty_shape(self) -> None:
        output = self.run_source(
            """
craft increment(present, current) {
    when present {
        yield current + 1
    } otherwise {
        yield 1
    }
}
make stats := map_new()
make once := map_alter(stats, "auth", increment)
make twice := map_alter(once, "auth", increment)
make empty := analysis_empty()
emit twice["auth"]
emit empty["total_lines"]
emit size(empty["by_service"])
"""
        )
        self.assertEqual(output, ["2", "0", "0"])

    def test_each_accepts_a_stream(self) -> None:
        output = self.run_source(
            """
make total := 0
each item in ([1, 2, 3] :: stream()) {
    change total := total + item
}
emit total
"""
        )
        self.assertEqual(output, ["6"])

    def test_stream_source_size_is_bounded_at_creation(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "stream item limit"):
            self.run_source(
                """
make items := [1, 2, 3] :: stream()
""",
                max_collection_items=2,
            )


if __name__ == "__main__":
    unittest.main()
