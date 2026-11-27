from __future__ import annotations

import unittest

from reaper import Interpreter, ParseError, ReaperRuntimeError
from reaper.parser import parse
from reaper.typecheck import check_source


class ScenarioFlowTests(unittest.TestCase):
    SOURCE = """
scenario operanda(num; sum; bounds) {
    reg it := num
    reg regit := sum
    each value in bounds {
        when value == 0 {
            continue
        }
        change regit := regit + value
    }
    yield regit + it
}
emit operanda(2; 10; 0...3)
"""

    def run_source(self, engine: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(self.SOURCE, engine=engine)
        return output

    def test_scenario_registers_ranges_and_continue_match_in_both_engines(self) -> None:
        self.assertEqual(self.run_source("treewalk"), ["18"])
        self.assertEqual(self.run_source("vm"), ["18"])

    def test_inclusive_ranges_support_ascending_and_descending_bounds(self) -> None:
        source = """
each item in 0...2 {
    emit item
}
each item in 2..0 {
    emit item
}
"""
        expected = ["0", "1", "2", "2", "1", "0"]
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, expected)

    def test_registers_are_numeric_at_runtime(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "'reg' requires a finite numeric value"):
            Interpreter(output=lambda _line: None).run('reg status := "ready"')
        with self.assertRaisesRegex(ReaperRuntimeError, "only accepts finite numeric values"):
            Interpreter(output=lambda _line: None).run('reg count := 1\nchange count := "one"')

    def test_numeric_registers_accept_integer_and_float_assignments(self) -> None:
        source = "reg ratio := 1; change ratio := 1.5; emit ratio"
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["1.5"])
        self.assertTrue(check_source(source).ok)

    def test_register_and_range_types_are_checked(self) -> None:
        valid = check_source("""
scenario total() {
    reg result := 0
    each value in 0...4 {
        change result := result + value
    }
    yield result
}
emit total()
""")
        self.assertTrue(valid.ok, valid.as_dict())

        invalid = check_source('reg label := "not numeric"')
        self.assertFalse(invalid.ok)
        self.assertEqual(invalid.diagnostics[0].code, "RPR-T0004")

    def test_semicolon_separates_statements_and_list_items(self) -> None:
        source = """
scenario noop() { yield; }
noop(); reg total := 1; change total := total + 2; emit [total; 4; 5]
"""
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["[3, 4, 5]"])

    def test_continue_targets_nearest_nested_loop_and_works_in_while(self) -> None:
        source = """
reg total := 0
each outer in 1...2 {
    each inner in 1...3 {
        when inner == 2 {
            continue
        }
        change total := total + outer * 10 + inner
    }
}
reg index := 0
loop while index < 4 {
    change index := index + 1
    when index == 2 {
        continue
    }
    change total := total + index
}
emit total
"""
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["76"])

    def test_inclusive_ranges_enforce_integer_bounds_and_collection_quota(self) -> None:
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine, case="float-bound"):
                with self.assertRaisesRegex(ReaperRuntimeError, "whole-number bounds"):
                    Interpreter(output=lambda _line: None).run("emit 0.5...2", engine=engine)
            with self.subTest(engine=engine, case="quota"):
                with self.assertRaisesRegex(ReaperRuntimeError, "range item limit"):
                    Interpreter(output=lambda _line: None, max_collection_items=2).run(
                        "emit 0...2", engine=engine
                    )

    def test_continue_outside_a_loop_is_rejected(self) -> None:
        with self.assertRaisesRegex(ParseError, "only be used inside a loop"):
            parse("continue")

    def test_nested_function_does_not_inherit_outer_loop_context(self) -> None:
        with self.assertRaisesRegex(ParseError, "only be used inside a loop"):
            parse("""
each item in 0...1 {
    craft invalid() {
        continue
    }
}
""")


if __name__ == "__main__":
    unittest.main()
