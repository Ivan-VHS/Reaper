from __future__ import annotations

import unittest

from reaper import ExecutionLimitError, Interpreter, ReaperRuntimeError


class FlowToolkitTests(unittest.TestCase):
    def execute(self, source: str, engine: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, engine=engine)
        return output

    def test_predicate_combinators_and_search_work_in_both_engines(self) -> None:
        source = """
        craft positive(value) { yield value > 0 }
        emit [2, 4] :: all(positive)
        emit [0, 1] :: any(positive)
        emit [0] :: none(positive)
        emit [0, 1, 2] :: count(positive)
        emit [0, 4, 7] :: find(positive)
        emit [0, 4, 7] :: find_index(positive)
        """
        expected = ["true", "true", "true", "2", "4", "1"]
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.execute(source, engine), expected)

    def test_sequence_flow_combinators_work_in_both_engines(self) -> None:
        source = """
        craft positive(value) { yield value > 0 }
        craft add(left, right) { yield left + right }
        emit [1, 2, 3, 0, 4] :: take_while(positive)
        emit [1, 2, 3, 0, 4] :: drop_while(positive)
        emit enumerate(["a", "b"], 5)
        emit zip([1, 2, 3], ["a", "b"])
        emit [1, 2, 3] :: scan(0, add)
        emit window([1, 2, 3, 4], 2)
        emit window([1, 2, 3, 4, 5], 2, 2)
        """
        expected = [
            "[1, 2, 3]",
            "[0, 4]",
            "[[5, a], [6, b]]",
            "[[1, a], [2, b]]",
            "[1, 3, 6]",
            "[[1, 2], [2, 3], [3, 4]]",
            "[[1, 2], [3, 4]]",
        ]
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.execute(source, engine), expected)

    def test_predicates_short_circuit(self) -> None:
        source = """
        craft positive(value) {
            when value == 0 { yield false }
            yield true
        }
        emit [0, 1, 2] :: any(positive)
        emit [1, 0, 2] :: all(positive)
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.execute(source, engine), ["true", "false"])

    def test_empty_sequence_semantics(self) -> None:
        source = """
        craft positive(value) { yield value > 0 }
        emit [] :: all(positive)
        emit [] :: any(positive)
        emit [] :: none(positive)
        emit [] :: count(positive)
        emit [] :: find(positive)
        emit [] :: find_index(positive)
        emit [] :: take_while(positive)
        emit [] :: drop_while(positive)
        """
        expected = ["true", "false", "true", "0", "nothing", "nothing", "[]", "[]"]
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.execute(source, engine), expected)

    def test_argument_and_collection_limits_are_enforced(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "window width must be positive"):
            Interpreter(output=lambda _line: None).run("emit window([1, 2], 0)")
        with self.assertRaisesRegex(ReaperRuntimeError, "enumerate start must be a whole number"):
            Interpreter(output=lambda _line: None).run('emit enumerate([1], "zero")')
        with self.assertRaisesRegex(ReaperRuntimeError, "expected a Reaper function"):
            Interpreter(output=lambda _line: None).run("emit [1] :: all(1)")
        with self.assertRaises(ExecutionLimitError):
            Interpreter(output=lambda _line: None, max_steps=8).run(
                "craft yes(value) { yield true }\nemit [1, 2, 3, 4] :: all(yes)"
            )


if __name__ == "__main__":
    unittest.main()
