from __future__ import annotations

import math
import unittest

from reaper import Interpreter
from reaper import metric_space as metric


class MetricSpaceTests(unittest.TestCase):
    def test_euclidean_and_orthogonality(self) -> None:
        self.assertEqual(metric.vector_norm([3, 4]), 5.0)
        self.assertEqual(metric.euclidean_distance([3, 4], [0, 0]), 5.0)
        self.assertEqual(metric.dot([3, 4], [0, 2]), 8.0)
        self.assertTrue(metric.is_orthogonal([1, 0], [0, 1]))
        self.assertFalse(metric.is_orthogonal([1, 1], [1, 0]))

    def test_quadratic_form_and_triangle_models(self) -> None:
        self.assertEqual(metric.quadratic_form([3, 4], [[2, 0], [0, 3]]), 66.0)
        self.assertAlmostEqual(metric.law_of_cosines(3, 4, math.pi / 2), 5.0)
        self.assertEqual(metric.de_gua_area(3, 4, 12), 13.0)
        self.assertAlmostEqual(metric.reciprocal_altitude(3, 4), 2.4)

    def test_parseval_and_unit_circle(self) -> None:
        self.assertEqual(metric.parseval_energy([1, 2, 2]), 9.0)
        self.assertLess(metric.unit_circle_residual(0.73), 1e-12)

    def test_non_euclidean_and_statistical_models(self) -> None:
        self.assertGreater(metric.spherical_hypotenuse(0.2, 0.3), 0.0)
        self.assertGreater(metric.hyperbolic_hypotenuse(0.2, 0.3), 0.0)
        self.assertEqual(metric.minkowski_interval(10, [3, 4, 0]), 75.0)
        self.assertEqual(metric.combine_uncorrelated_variances([4, 9, 3]), 16.0)

    def test_invalid_dimensions_and_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "same dimension"):
            metric.euclidean_distance([1, 2], [1])
        with self.assertRaisesRegex(TypeError, "real number"):
            metric.vector_norm([True])
        with self.assertRaisesRegex(ValueError, "negative"):
            metric.combine_uncorrelated_variances([1, -1])
        with self.assertRaisesRegex(ValueError, "pi/2"):
            metric.spherical_hypotenuse(2, 0.1)
        with self.assertRaisesRegex(ValueError, "positive"):
            metric.reciprocal_altitude(0, 2)

    def test_language_builtins(self) -> None:
        output: list[str] = []
        source = """
        emit vector_norm([3, 4])
        emit euclidean_distance([3, 4], [0, 0])
        emit is_orthogonal([1, 0], [0, 1])
        emit quadratic_form([3, 4], [[2, 0], [0, 3]])
        emit parseval_energy([1, 2, 2])
        emit minkowski_interval(10, [3, 4, 0])
        emit combine_variances([4, 9, 3])
        emit reciprocal_altitude(3, 4)
        """
        Interpreter(output=output.append).run(source)
        self.assertEqual(output[:3], ["5.0", "5.0", "true"])
        self.assertEqual(output[3:], ["66.0", "9.0", "75.0", "16.0", "2.4"])


if __name__ == "__main__":
    unittest.main()
