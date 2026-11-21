from __future__ import annotations

import math
import unittest

from reaper import Interpreter
from reaper import metric_space as metric


class ExtendedMetricTests(unittest.TestCase):
    def test_norm_families_and_normalization(self) -> None:
        self.assertEqual(metric.vector_norm([3, -4], "l1"), 7.0)
        self.assertEqual(metric.vector_norm([3, -4], "l2"), 5.0)
        self.assertEqual(metric.vector_norm([3, -4], "linf"), 4.0)
        self.assertEqual(metric.normalize([3, 4]), [0.6, 0.8])

    def test_distance_families(self) -> None:
        self.assertEqual(metric.manhattan_distance([3, 4], [0, 0]), 7.0)
        self.assertEqual(metric.chebyshev_distance([3, 4], [0, 0]), 4.0)
        self.assertEqual(metric.squared_euclidean_distance([3, 4], [0, 0]), 25.0)

    def test_angle_similarity_projection_and_centroid(self) -> None:
        self.assertAlmostEqual(metric.cosine_similarity([1, 0], [1, 1]), 1 / math.sqrt(2))
        self.assertAlmostEqual(metric.angle_between([1, 0], [0, 1]), math.pi / 2)
        self.assertEqual(metric.project([3, 4], [1, 0]), [3.0, 0.0])
        self.assertEqual(metric.centroid([[0, 2], [2, 4], [4, 6]]), [2.0, 4.0])

    def test_undefined_and_invalid_metric_cases(self) -> None:
        with self.assertRaisesRegex(ValueError, "zero vector"):
            metric.normalize([0, 0])
        with self.assertRaisesRegex(ValueError, "zero vector"):
            metric.cosine_similarity([1, 2], [0, 0])
        with self.assertRaisesRegex(ValueError, "zero vector"):
            metric.project([1, 2], [0, 0])
        with self.assertRaisesRegex(ValueError, "norm kind"):
            metric.vector_norm([1, 2], "l3")
        with self.assertRaisesRegex(ValueError, "same dimension"):
            metric.manhattan_distance([1], [1, 2])

    def test_language_exposes_extended_metrics(self) -> None:
        output: list[str] = []
        Interpreter(output=output.append).run("""
        emit vector_norm([3, 4], "l1")
        emit vector_normalize([3, 4])
        emit manhattan_distance([3, 4], [0, 0])
        emit chebyshev_distance([3, 4], [0, 0])
        emit squared_euclidean_distance([3, 4], [0, 0])
        emit cosine_similarity([1, 0], [0, 1])
        emit angle_between([1, 0], [0, 1])
        emit vector_projection([3, 4], [1, 0])
        emit vector_centroid([[0, 2], [2, 4]])
        """)
        self.assertEqual(output[0:1], ["7.0"])
        self.assertEqual(output[1], "[0.6, 0.8]")
        self.assertEqual(output[2:5], ["7.0", "4.0", "25.0"])
        self.assertEqual(output[5], "0.0")
        self.assertEqual(output[7:], ["[3.0, 0.0]", "[1.0, 3.0]"])


if __name__ == "__main__":
    unittest.main()
