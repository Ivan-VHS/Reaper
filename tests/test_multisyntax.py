from __future__ import annotations

import unittest

from reaper.multisyntax import (
    MultiSyntaxError, analyze_brainfuck, detect_syntax, list_syntaxes,
    parse_polyglot, run_polyglot, run_source,
)


class SyntaxRegistryTests(unittest.TestCase):
    def test_registry_exposes_multiple_programming_paradigms(self):
        names = {item["name"] for item in list_syntaxes()}
        self.assertEqual(names, {"reaper", "python", "pipeline", "lisp", "forth", "brainfuck", "befunge93"})

    def test_syntax_detection_uses_extension_and_source_marker(self):
        self.assertEqual(detect_syntax("sample.py"), "python")
        self.assertEqual(detect_syntax("sample.bf"), "brainfuck")
        self.assertEqual(detect_syntax("sample.unknown", source="#!syntax lisp\n(+ 1 2)"), "lisp")
        self.assertEqual(detect_syntax("sample.rpr"), "reaper")


class PythonSubsetTests(unittest.TestCase):
    def test_bindings_functions_lambdas_and_destructuring(self):
        output = []
        source = (
            "left, right = (4, 5)\n"
            "def combine(a: int, b: int) -> int:\n"
            "    return a * 10 + b\n"
            "print(combine(left, right))\n"
            "print(list(map(lambda item: item * 2, [1, 2, 3])))\n"
        )
        result = run_source("python", source, output=output.append)
        self.assertEqual(output, ["45\n", "[2, 4, 6]\n"])
        self.assertEqual(result["syntax"], "python")

    def test_pattern_matching_and_short_circuit(self):
        output = []
        source = (
            "value: int = 7\n"
            "match value:\n"
            "    case 7:\n"
            "        print('seven')\n"
            "    case _:\n"
            "        print('other')\n"
            "print(False and missing_name)\n"
        )
        run_source("python", source, output=output.append)
        self.assertEqual(output, ["seven\n", "False\n"])

    def test_loop_else_and_break_semantics(self):
        output = []
        source = (
            "for value in range(3):\n"
            "    if value == 1:\n"
            "        break\n"
            "else:\n"
            "    print('completed')\n"
            "print('done')\n"
        )
        run_source("python", source, output=output.append)
        self.assertEqual(output, ["done\n"])

    def test_python_subset_rejects_imports_and_attribute_access(self):
        with self.assertRaises(MultiSyntaxError):
            run_source("python", "import os")
        with self.assertRaises(MultiSyntaxError):
            run_source("python", "print((1).__class__)")

    def test_python_execution_is_bounded(self):
        with self.assertRaisesRegex(MultiSyntaxError, "step limit"):
            run_source("python", "while True:\n    pass", max_steps=20)


class PipelineTests(unittest.TestCase):
    def test_pipeline_applies_data_transformations_left_to_right(self):
        result = run_source(
            "pipeline",
            "[1, 2, 3, 4] |> map(lambda item: item * 2) |> filter(lambda item: item > 4) |> sum",
        )
        self.assertEqual(result["result"], 14)

    def test_pipeline_supports_text_and_arrow_separator(self):
        result = run_source("pipeline", '"  reaper  " -> trim -> upper')
        self.assertEqual(result["result"], "REAPER")

    def test_pipeline_rejects_unknown_stages(self):
        with self.assertRaisesRegex(MultiSyntaxError, "unknown pipeline"):
            run_source("pipeline", "[1, 2] |> magic")


class LispTests(unittest.TestCase):
    def test_definitions_closures_and_higher_order_list_operations(self):
        output = []
        source = (
            "(define (square value) (* value value))\n"
            "(define doubled (lambda (value) (* value 2)))\n"
            "(display (square 5))\n"
            "(display (map doubled '(1 2 3)))\n"
        )
        # Quote returns the parsed list as data; symbol resolution is not performed.
        run_source("lisp", source, output=output.append)
        self.assertEqual(output, ["25", "(2 4 6)"])

    def test_lisp_let_if_and_balanced_reader(self):
        output = []
        run_source("lisp", "(display (let ((answer 42)) (if (> answer 10) answer 0)))", output=output.append)
        self.assertEqual(output, ["42"])
        with self.assertRaisesRegex(MultiSyntaxError, "unclosed"):
            run_source("lisp", "(+ 1 2")

    def test_lisp_rejects_unknown_symbols(self):
        with self.assertRaisesRegex(MultiSyntaxError, "unknown Lisp symbol"):
            run_source("lisp", "(not-defined 1)")


class ForthTests(unittest.TestCase):
    def test_stack_operations_and_colon_definitions(self):
        output = []
        result = run_source("forth", ": square dup * ; 5 square .", output=output.append)
        self.assertEqual(output, ["25 "])
        self.assertEqual(result["result"], [])

    def test_stack_is_reported_without_implicit_output(self):
        result = run_source("forth", "10 20 30 swap")
        self.assertEqual(result["result"], [10, 30, 20])

    def test_stack_underflow_is_explicit(self):
        with self.assertRaisesRegex(MultiSyntaxError, "underflow"):
            run_source("forth", "dup")


class BrainfuckTests(unittest.TestCase):
    def test_eight_commands_execute_with_wrapping(self):
        output = []
        result = run_source("brainfuck", "++++++++[>++++++++<-]>+.", output=output.append)
        self.assertEqual(output, ["A"])
        self.assertEqual(result["result"]["pointer"], 1)

    def test_bracket_pairs_and_clean_pointer_loop(self):
        report = analyze_brainfuck("[->+<]")
        self.assertTrue(report["validated"])
        self.assertEqual(report["loop_pairs"], 1)
        self.assertEqual(report["pointer_balance_warnings"], [])

    def test_non_balanced_loop_is_reported_without_rejecting_program(self):
        report = analyze_brainfuck("[>+]")
        self.assertEqual(report["pointer_balance_warnings"][0]["textual_pointer_delta"], 1)

    def test_unmatched_brackets_are_rejected_before_execution(self):
        with self.assertRaisesRegex(MultiSyntaxError, "unmatched"):
            run_source("brainfuck", "[++")
        with self.assertRaisesRegex(MultiSyntaxError, "unmatched"):
            run_source("brainfuck", "++]")

    def test_tape_bounds_are_enforced(self):
        with self.assertRaisesRegex(MultiSyntaxError, "right edge"):
            run_source("brainfuck", ">", tape_size=1)
        with self.assertRaisesRegex(MultiSyntaxError, "left of tape"):
            run_source("brainfuck", "<")

    def test_input_eof_modes_are_explicit(self):
        zero = run_source("brainfuck", ",.", eof_mode="zero")
        maximum = run_source("brainfuck", ",.", eof_mode="max")
        self.assertEqual(zero["result"]["output_bytes"], [0])
        self.assertEqual(maximum["result"]["output_bytes"], [255])


class BefungeTests(unittest.TestCase):
    def test_two_dimensional_stack_program(self):
        output = []
        result = run_source("befunge93", "23+.@", output=output.append)
        self.assertEqual(output, ["5 "])
        self.assertTrue(result["result"]["halted"])

    def test_playfield_dimensions_are_bounded(self):
        with self.assertRaisesRegex(MultiSyntaxError, "80 columns"):
            run_source("befunge93", "1" * 81)


class PolyglotTests(unittest.TestCase):
    def test_polyglot_blocks_run_in_source_order(self):
        source = (
            "%% python\n"
            "print(1 + 2)\n"
            "%% forth\n"
            "4 5 + .\n"
            "%% brainfuck\n"
            "++++++++[>++++++++<-]>+.\n"
        )
        result = run_polyglot(source)
        self.assertEqual(result["block_count"], 3)
        self.assertEqual([item["syntax"] for item in result["blocks"]], ["python", "forth", "brainfuck"])
        self.assertEqual(result["output"], ["3\n", "9 ", "A"])
        self.assertEqual([item["output"] for item in result["blocks"]], [["3\n"], ["9 "], ["A"]])

    def test_polyglot_parser_requires_headers_and_known_syntaxes(self):
        with self.assertRaisesRegex(MultiSyntaxError, "start with"):
            parse_polyglot("print(1)")
        with self.assertRaises(MultiSyntaxError):
            parse_polyglot("%% unknown\nbody")

    def test_native_reaper_syntax_remains_available(self):
        output = []
        run_source("reaper", 'make answer := 42\nemit answer', output=output.append)
        self.assertEqual(output, ["42"])


if __name__ == "__main__":
    unittest.main()
