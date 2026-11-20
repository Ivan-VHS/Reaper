from __future__ import annotations

import unittest

from reaper.self_product import MAX_DEPTH, vertical_self_product


class VerticalSelfProductTests(unittest.TestCase):
    def test_pipeline_is_squared_at_each_vertical_level(self) -> None:
        report = vertical_self_product(
            0,
            (lambda value: value + 1, lambda value: value * 2),
            depth=2,
        )
        # F(x)=(x+1)*2; F²(0)=6 and F⁴(0)=30.
        self.assertEqual(report.layers[0].value, 6)
        self.assertEqual(report.layers[1].value, 30)
        self.assertEqual(report.result, 30)
        self.assertEqual(report.pipeline_applications, 4)
        self.assertEqual(report.function_calls, 8)
        self.assertEqual(report.layers[0].pipeline_applications, 2)
        self.assertEqual(report.layers[1].pipeline_applications, 4)

    def test_single_level_reuses_the_same_pipeline_twice(self) -> None:
        report = vertical_self_product(3, (lambda value: value + 4,), depth=1)
        self.assertEqual(report.result, 11)
        self.assertEqual(report.transform_count, 1)
        self.assertEqual(report.pipeline_applications, 2)

    def test_rejects_empty_or_non_callable_pipeline(self) -> None:
        with self.assertRaisesRegex(ValueError, "1.."):
            vertical_self_product(0, (), depth=1)
        with self.assertRaisesRegex(TypeError, "callable"):
            vertical_self_product(0, (42,), depth=1)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            vertical_self_product(0, "not a pipeline", depth=1)  # type: ignore[arg-type]

    def test_depth_is_type_checked_and_bounded(self) -> None:
        with self.assertRaises(TypeError):
            vertical_self_product(0, (lambda value: value,), depth=True)
        with self.assertRaises(ValueError):
            vertical_self_product(0, (lambda value: value,), depth=0)
        with self.assertRaises(ValueError):
            vertical_self_product(0, (lambda value: value,), depth=MAX_DEPTH + 1)


if __name__ == "__main__":
    unittest.main()
