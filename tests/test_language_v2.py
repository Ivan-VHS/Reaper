from __future__ import annotations

import unittest

from reaper import Interpreter, ParseError, ReaperRuntimeError


class ModernSyntaxTests(unittest.TestCase):
    def capture(self, source: str, engine: str = "treewalk") -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, engine=engine)
        return output

    def test_modern_declarations_functions_and_if_else(self) -> None:
        source = """
        let factor = 3
        fn scale(value) {
            return value * factor
        }
        mut total = 0
        for number in [1, 2, 3] {
            if number == 2 {
                continue
            } else {
                total = total + scale(number)
            }
        }
        emit total
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.capture(source, engine), ["12"])

    def test_break_continue_and_while_in_both_engines(self) -> None:
        source = """
        mut total = 0
        for number in range(1, 5) {
            if number == 2 {
                continue
            }
            total = total + number
            if total >= 4 {
                break
            }
        }
        mut cursor = 0
        mut steps = 0
        while cursor < 10 {
            cursor = cursor + 1
            if cursor == 4 {
                continue
            }
            if cursor == 7 {
                break
            }
            steps = steps + 1
        }
        emit [total, cursor, steps]
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.capture(source, engine), ["[4, 7, 5]"])

    def test_nested_loops_break_only_the_nearest_loop(self) -> None:
        source = """
        mut total = 0
        for outer in [1, 2, 3] {
            for inner in [1, 2, 3] {
                if inner == 2 {
                    break
                }
                total = total + outer * inner
            }
        }
        emit total
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.capture(source, engine), ["6"])

    def test_map_literals_member_access_membership_and_coalescing(self) -> None:
        source = """
        let settings = {
            "name": "Reaper",
            "runtime": {"major": 0, "stable": true},
        }
        emit settings.name
        emit settings.runtime.major
        emit "runtime" in settings
        emit "missing" in settings
        emit nothing ?? "fallback"
        emit "kept" ?? "not-used"
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(
                    self.capture(source, engine),
                    ["Reaper", "0", "true", "false", "fallback", "kept"],
                )

    def test_map_iteration_visits_keys_in_insertion_order(self) -> None:
        source = """
        let values = {"alpha": 1, "beta": 2, "gamma": 3}
        mut result = []
        for key in values {
            result = push(result, key)
        }
        emit result
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.capture(source, engine), ["[alpha, beta, gamma]"])

    def test_null_coalescing_is_lazy(self) -> None:
        source = """
        fn explode() {
            return 1 / 0
        }
        emit 42 ?? explode()
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.capture(source, engine), ["42"])

    def test_new_russian_aliases_execute_in_both_engines(self) -> None:
        source = """
        связать base = 10
        процедура scale(value) {
            возврат value * base
        }
        изменяемый total = 0
        для_каждого item в [1, 2, 3, 4] {
            условие item == 2 {
                продолжить
            }
            total = total + scale(item)
            условие total >= 40 {
                прервать
            }
        }
        вывести total
        """
        for engine in ("treewalk", "vm"):
            with self.subTest(engine=engine):
                self.assertEqual(self.capture(source, engine), ["40"])

    def test_modern_declaration_is_immutable_or_mutable_as_declared(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "cannot be changed"):
            self.capture("let fixed = 1\nfixed = 2")
        self.assertEqual(self.capture("mut value = 1\nvalue = 2\nemit value"), ["2"])

    def test_break_cannot_escape_a_function_boundary(self) -> None:
        source = """
        fn invalid() {
            break
        }
        invalid()
        """
        with self.assertRaisesRegex(ReaperRuntimeError, "break cannot cross a function boundary"):
            self.capture(source)

    def test_break_and_continue_outside_loops_are_language_errors_in_both_engines(self) -> None:
        for keyword in ("break", "continue"):
            for engine in ("treewalk", "vm"):
                with self.subTest(keyword=keyword, engine=engine):
                    with self.assertRaisesRegex(ReaperRuntimeError, f"{keyword} can only be used inside a loop"):
                        self.capture(keyword, engine)

    def test_parse_errors_keep_source_locations_for_new_syntax(self) -> None:
        with self.assertRaisesRegex(ParseError, r"<memory>:1:"):
            self.capture("fn broken( { return 1 }")


if __name__ == "__main__":
    unittest.main()
