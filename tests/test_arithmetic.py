from __future__ import annotations

import unittest

from reaper.arithmetic import (
    accumulate, aggregate, amplify, cartesianize, combine, compute, compound,
    convolve, couple, cross_multiply, expand, exponentiate, factor, fuse,
    multiply, pair, product, scale,
)
from reaper import Interpreter, ReaperRuntimeError


class ArithmeticOperationsTests(unittest.TestCase):
    def test_scalar_and_vector_multiply(self):
        self.assertEqual(multiply(6, 7), 42)
        self.assertEqual(product([2, 3, 4]), 24)
        self.assertEqual(scale([1, 2, 3], 2), [2, 4, 6])
        self.assertEqual(amplify(2.5, 4), 10.0)
        self.assertEqual(compound([1, 2], [3, 4]), [3, 8])

    def test_compute_dispatch_and_exponentiation(self):
        self.assertEqual(compute(7, 5, "add"), 12)
        self.assertEqual(compute(7, 5, "subtract"), 2)
        self.assertEqual(compute(7, 5), 35)
        self.assertEqual(exponentiate(2, 8), 256.0)

    def test_sequence_expansion_and_accumulation(self):
        self.assertEqual(expand([1, 2], 3), [1, 2, 1, 2, 1, 2])
        self.assertEqual(accumulate([1, 2, 3, 4]), [1, 3, 6, 10])

    def test_outer_product_and_cartesian_product(self):
        self.assertEqual(cross_multiply([1, 2], [3, 4]), [[3, 4], [6, 8]])
        self.assertEqual(cartesianize(["a", "b"], [1, 2]), [
            ["a", 1], ["a", 2], ["b", 1], ["b", 2]
        ])

    def test_factorization_and_composition(self):
        self.assertEqual(factor(360), [2, 2, 2, 3, 3, 5])
        self.assertEqual(combine([1, 2], [3, 4]), [4, 6])
        self.assertEqual(fuse([1, 2], [3]), [1, 2, 3])
        self.assertEqual(pair("x", 2), ["x", 2])
        self.assertEqual(couple(["a", "b"], [1, 2]), [["a", 1], ["b", 2]])

    def test_aggregation_and_convolution(self):
        self.assertEqual(aggregate([1, 2, 3])["mean"], 2)
        self.assertEqual(aggregate([1, 2, 3])["product"], 6)
        self.assertEqual(convolve([1, 2, 3], [1, 1]), [1.0, 3.0, 5.0, 3.0])

    def test_rejects_invalid_and_oversized_values(self):
        for call in (
            lambda: multiply(True, 2),
            lambda: factor(0),
            lambda: exponentiate(0, -1),
            lambda: compute(1, 0, "divide"),
            lambda: combine([1], [1, 2]),
            lambda: couple([1], [1, 2]),
            lambda: convolve([], [1]),
            lambda: aggregate([]),
        ):
            with self.assertRaises((TypeError, ValueError, OverflowError)):
                call()

    def test_runtime_builtins_are_exposed(self):
        output = []
        Interpreter(output=output.append).run("""
        make values := accumulate([1, 2, 3])
        emit multiply(6, 7)
        emit product(values)
        emit cartesianize([1, 2], [3])
        """)
        self.assertEqual(output, ["42", "18", "[[1, 3], [2, 3]]"])

    def test_runtime_iterate_builtin(self):
        output = []
        Interpreter(output=output.append).run("""
        craft step(value) { yield value * 2 }
        emit iterate(2, 3, step)
        """)
        self.assertEqual(output, ["[2, 4, 8, 16]"])

    def test_runtime_rejects_operation_errors_as_language_errors(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "factor"):
            Interpreter(output=lambda _line: None).run("emit factor(0)")


if __name__ == "__main__":
    unittest.main()
