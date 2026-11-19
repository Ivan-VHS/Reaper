from __future__ import annotations

import unittest
from fractions import Fraction

from reaper.decomposition import (
    decompose_sequence, distribute_weighted, divide_fraction,
    euclidean_divmod, factor_pairs, recombine, split_evenly,
)


class EuclideanDivisionTests(unittest.TestCase):
    def test_positive_and_negative_divisors(self) -> None:
        for a, b, q, r in [(17, 5, 3, 2), (-17, 5, -4, 3),
                           (17, -5, -3, 2), (-17, -5, 4, 3)]:
            result = euclidean_divmod(a, b)
            self.assertEqual((result.quotient, result.remainder), (q, r))
            self.assertTrue(result.verify())
            self.assertGreaterEqual(r, 0)
            self.assertLess(r, abs(b))

    def test_exact_and_non_exact(self) -> None:
        self.assertTrue(euclidean_divmod(24, 6).exact)
        self.assertFalse(euclidean_divmod(25, 6).exact)

    def test_zero_divisor_and_invalid_types(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            euclidean_divmod(1, 0)
        with self.assertRaises(TypeError):
            euclidean_divmod(True, 2)

    def test_exact_fraction_division(self) -> None:
        self.assertEqual(divide_fraction(Fraction(1, 3), 2), Fraction(1, 6))
        with self.assertRaises(ZeroDivisionError):
            divide_fraction(1, 0)


class DistributionTests(unittest.TestCase):
    def test_even_split_conserves_positive_and_negative_totals(self) -> None:
        self.assertEqual(split_evenly(11, 4), (3, 3, 3, 2))
        self.assertEqual(split_evenly(-11, 4), (-3, -3, -3, -2))
        self.assertEqual(sum(split_evenly(11, 4)), 11)

    def test_weighted_split_uses_largest_remainder_and_stable_ties(self) -> None:
        self.assertEqual(distribute_weighted(10, [1, 1, 1]), (4, 3, 3))
        self.assertEqual(distribute_weighted(10, [1, 2, 1]), (3, 5, 2))
        self.assertEqual(distribute_weighted(-10, [1, 1]), (-5, -5))
        self.assertEqual(sum(distribute_weighted(97, [0, 2, 3])), 97)

    def test_invalid_distributions(self) -> None:
        for weights in ([], [0, 0], [-1, 2]):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                distribute_weighted(10, weights)
        with self.assertRaises(ValueError):
            split_evenly(10, 0)


class DecompositionTests(unittest.TestCase):
    def test_partition_and_recombine_are_order_preserving(self) -> None:
        source = tuple(range(10))
        parts = decompose_sequence(source, 3)
        self.assertEqual(parts, ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)))
        self.assertEqual(recombine(parts), source)

    def test_empty_and_invalid_chunk(self) -> None:
        self.assertEqual(decompose_sequence([], 4), ())
        with self.assertRaises(ValueError):
            decompose_sequence([1], 0)

    def test_factor_pairs(self) -> None:
        self.assertEqual(factor_pairs(36), ((1, 36), (2, 18), (3, 12), (4, 9), (6, 6)))
        with self.assertRaises(ValueError):
            factor_pairs(0)


if __name__ == "__main__":
    unittest.main()
