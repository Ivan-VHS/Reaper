from __future__ import annotations

import unittest

from reaper import Interpreter, ReaperRuntimeError


class AlgebraicOperatorTests(unittest.TestCase):
    def capture(self, source: str, **limits: int) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, **limits).run(source)
        return output

    def test_scalar_algebra(self) -> None:
        self.assertEqual(
            self.capture("""
            emit opposite(4)
            emit multiply(6, 7)
            emit divide(9, 3)
            emit power(2, 8)
            emit root(81, 4)
            emit logarithm(100, 10)
            emit exponential(3, 2)
            """),
            ["-4", "42", "3.0", "256", "3.0", "2.0", "8.0"],
        )

    def test_real_domain_validation(self) -> None:
        for source in ("emit root(-4, 2)", "emit logarithm(0)",
                       "emit divide(1, 0)", "emit normalize([1, 2], \"unknown\")"):
            with self.subTest(source=source), self.assertRaises(ReaperRuntimeError):
                self.capture(source)

    def test_vector_and_matrix_operations(self) -> None:
        self.assertEqual(
            self.capture("""
            emit vector_scale([1, 2, 3], 3)
            emit dot([1, 2, 3], [4, 5, 6])
            emit distance([0, 0], [3, 4])
            emit transpose([[1, 2], [3, 4]])
            emit matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
            """),
            ["[3, 6, 9]", "32", "5.0", "[[1, 3], [2, 4]]", "[[19, 22], [43, 50]]"],
        )

    def test_discrete_calculus_and_accumulation(self) -> None:
        self.assertEqual(
            self.capture("""
            emit differentiate([1, 3, 6], 0.5)
            emit integrate([1, 3, 6], 0.5)
            emit accumulate([1, 2, 3], 10)
            emit differences([2, 5, 9])
            """),
            ["[4.0, 6.0]", "[0, 1.0, 3.25]", "[11, 13, 16]", "[3, 4]"],
        )

    def test_normalization_quantization_and_factorization(self) -> None:
        self.assertEqual(
            self.capture("""
            emit normalize([10, 20, 30])
            emit normalize([3, 4], "unit")
            emit quantize(1.26, 0.25)
            emit factorize(360)
            """),
            ["[0.0, 0.5, 1.0]", "[0.6, 0.8]", "1.25", "[2, 2, 2, 3, 3, 5]"],
        )

    def test_collection_transforms(self) -> None:
        self.assertEqual(
            self.capture("""
            emit reverse([1, 2, 3])
            emit replicate("x", 3)
            emit flatten([1, [2, [3]], []])
            emit unique([1, true, 1, "1", true])
            emit cartesian([1, 2], ["a", "b"])
            emit proliferate([[1, 2], ["a", "b"]])
            """),
            ["[3, 2, 1]", "[x, x, x]", "[1, 2, 3]", "[1, true, 1]", "[[1, a], [1, b], [2, a], [2, b]]",
             "[[1, a], [1, b], [2, a], [2, b]]"],
        )

    def test_bounded_expansion_and_matrix_work(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            self.capture("emit replicate(0, 4)", max_collection_items=3)
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            self.capture("emit proliferate([[1, 2], [3, 4]])", max_collection_items=3)
        with self.assertRaisesRegex(ReaperRuntimeError, "matrix operation limit"):
            self.capture(
                "emit matrix_multiply([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "
                "[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])",
                max_steps=50,
            )

    def test_branch_runs_functions_without_host_effects(self) -> None:
        self.assertEqual(
            self.capture("""
            craft plus_one(value) { yield value + 1 }
            craft square(value) { yield value * value }
            emit branch(4, [plus_one, square])
            emit transform([1, 2, 3], plus_one)
            """),
            ["[5, 16]", "[2, 3, 4]"],
        )

    def test_branch_rejects_non_functions(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "Reaper function"):
            self.capture("emit branch(4, [1, 2])")


if __name__ == "__main__":
    unittest.main()
