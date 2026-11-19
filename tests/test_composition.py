from __future__ import annotations

import unittest

from reaper import Interpreter, ReaperRuntimeError


class CompositionTests(unittest.TestCase):
    def capture(self, source: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, "<composition-test>")
        return output

    def test_signature_compatible_builtin_pairs(self) -> None:
        helpers = """
        craft double(value) { yield value * 2 }
        craft is_even(value) { yield value % 2 == 0 }
        craft add(total, value) { yield total + value }
        """
        cases = {
            "map then size": ("emit range(1, 5) ~> map(double) ~> size()", ["4"]),
            "keep then sum": ("emit range(1, 5) ~> keep(is_even) ~> sum()", ["6"]),
            "push then sum": ("emit [1, 2, 3] ~> push(4) ~> sum()", ["10"]),
            "rest then first": ("emit [1, 2, 3] ~> rest() ~> first()", ["2"]),
            "sorted then first": ("emit [3, 1, 2] ~> sorted() ~> first()", ["1"]),
            "fold a sequence": ("emit [1, 2, 3] ~> fold(0, add)", ["6"]),
        }
        for label, (program, expected) in cases.items():
            with self.subTest(composition=label):
                self.assertEqual(self.capture(helpers + program), expected)

    def test_long_flow_composes_and_preserves_source(self) -> None:
        source = """
        craft double(value) { yield value * 2 }
        craft at_least_four(value) { yield value >= 4 }
        craft add(total, value) { yield total + value }

        make original := range(1, 5)
        make answer := original ~> map(double) ~> keep(at_least_four) ~> push(10) ~> sorted() ~> rest() ~> fold(0, add)
        emit answer
        emit original ~> sum()
        """
        self.assertEqual(self.capture(source), ["24", "10"])

    def test_incompatible_composition_fails_clearly(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "size"):
            self.capture("""
            craft double(value) { yield value * 2 }
            emit [1, 2] ~> map(double) ~> first() ~> size()
            """)


if __name__ == "__main__":
    unittest.main()
