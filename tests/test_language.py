from __future__ import annotations

import unittest

from reaper import ExecutionLimitError, Interpreter, LexError, ParseError, ReaperRuntimeError
from reaper.lexer import tokenize
from reaper.parser import parse
from reaper.operator_registry import OPERATOR_COUNT, operator_catalog, glyph_for_id, operator_by_glyph


class LexerTests(unittest.TestCase):
    def test_keywords_and_unicode_identifiers(self) -> None:
        tokens = tokenize("make утка := true # comment\nemit утка")
        self.assertEqual(
            [token.kind for token in tokens[:6]],
            ["MAKE", "IDENT", ":=", "TRUE", "NEWLINE", "EMIT"],
        )

    def test_string_escapes(self) -> None:
        self.assertEqual(tokenize('emit "a\\nb"')[1].value, "a\nb")

    def test_unterminated_string_is_reported(self) -> None:
        with self.assertRaises(LexError):
            tokenize('emit "unfinished')

    def test_operator_glyph_run_uses_maximal_munch(self) -> None:
        tokens = tokenize("value ::= 1 :: map(double) +::")
        self.assertEqual(
            [token.value for token in tokens if token.value],
            ["value", "::=", "1", "::", "map", "(", "double", ")", "+::"],
        )

    def test_unknown_glyph_runs_fail_early(self) -> None:
        with self.assertRaisesRegex(LexError, "unregistered"):
            tokenize("value +++++")
        with self.assertRaisesRegex(LexError, "five characters"):
            tokenize("value ::::::")


class ParserTests(unittest.TestCase):
    def test_malformed_declaration_has_location(self) -> None:
        with self.assertRaisesRegex(ParseError, r"<memory>:1:"):
            parse("make x = 2")


class OperatorRegistryTests(unittest.TestCase):
    def test_catalog_has_666_unique_round_trippable_ids(self) -> None:
        catalog = operator_catalog()
        self.assertEqual(len(catalog), OPERATOR_COUNT)
        self.assertEqual(len({item.glyph for item in catalog}), OPERATOR_COUNT)
        self.assertEqual([item.id for item in catalog], list(range(1, OPERATOR_COUNT + 1)))
        for operator_id in (1, 3, 48, 49, 120, 121, 240, 241, 360, 361, 480, 481, 580, 581, 666):
            self.assertEqual(operator_by_glyph(glyph_for_id(operator_id)).id, operator_id)
        self.assertEqual(glyph_for_id(49), ":::::")
        self.assertEqual(operator_by_glyph(":::::").status, "reserved")

    def test_catalog_has_exact_family_ranges(self) -> None:
        catalog = operator_catalog()
        self.assertEqual(sum(item.family == "memory" for item in catalog), 120)
        self.assertEqual(sum(item.family == "flow" for item in catalog), 120)
        self.assertEqual(sum(item.family == "binding" for item in catalog), 120)
        self.assertEqual(sum(item.family == "arithmetic" for item in catalog), 120)
        self.assertEqual(sum(item.family == "metric" for item in catalog), 100)
        self.assertEqual(sum(item.family == "system" for item in catalog), 86)


class RuntimeTests(unittest.TestCase):
    def capture(self, source: str, max_steps: int = 100_000) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, max_steps=max_steps).run(source)
        return output

    def test_hello_and_string_join(self) -> None:
        self.assertEqual(
            self.capture('make who := "world"\nemit "hello " ++ who'),
            ["hello world"],
        )

    def test_function_and_lexical_scope(self) -> None:
        source = """
        make factor := 3
        craft scale(value) {
            yield value * factor
        }
        emit scale(7)
        """
        self.assertEqual(self.capture(source), ["21"])

    def test_make_is_immutable(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "cannot be changed"):
            self.capture("make x := 1\nchange x := 2")

    def test_vary_can_change(self) -> None:
        self.assertEqual(
            self.capture("vary x := 1\nchange x := x + 4\nemit x"),
            ["5"],
        )

    def test_condition_and_otherwise(self) -> None:
        source = """
        make n := 4
        when n > 5 {
            emit "large"
        } otherwise {
            emit "small"
        }
        """
        self.assertEqual(self.capture(source), ["small"])

    def test_each_and_range(self) -> None:
        source = """
        vary total := 0
        each n in range(1, 5) {
            change total := total + n
        }
        emit total
        """
        self.assertEqual(self.capture(source), ["10"])

    def test_while_loop(self) -> None:
        source = """
        vary n := 0
        loop while n < 3 {
            change n := n + 1
        }
        emit n
        """
        self.assertEqual(self.capture(source), ["3"])

    def test_flow_map_keep_fold(self) -> None:
        source = """
        craft double(x) { yield x * 2 }
        craft large(x) { yield x >= 6 }
        craft add(a, b) { yield a + b }
        emit [1, 2, 3, 4] :: map(double) :: keep(large) :: fold(0, add)
        """
        self.assertEqual(self.capture(source), ["14"])

    def test_old_flow_operator_is_rejected(self) -> None:
        with self.assertRaises(LexError):
            tokenize("emit [1, 2] |> size()")

    def test_pipeline_accepts_single_argument_call(self) -> None:
        self.assertEqual(self.capture("emit [1, 2, 3] :: size()"), ["3"])

    def test_strict_definition_and_semicolon_separator(self) -> None:
        self.assertEqual(self.capture("make value ::= 7; emit value"), ["7"])

    def test_prefix_increment_mutates_only_vary_bindings(self) -> None:
        self.assertEqual(self.capture("vary count ::= 4\nemit :++count\nemit count"), ["5", "5"])
        with self.assertRaisesRegex(ReaperRuntimeError, "cannot be changed"):
            self.capture("make fixed ::= 4\nemit :++fixed")

    def test_list_concatenation_is_bounded(self) -> None:
        self.assertEqual(self.capture("emit [1, 2] ++: [3]"), ["[1, 2, 3]"])
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            interpreter.run("emit [1] ++: [2, 3]")

    def test_contract_equal_uses_strict_structural_equality(self) -> None:
        self.assertEqual(
            self.capture("emit [true] =:: [1]\nemit [1, 2] =:: [1, 2]"),
            ["false", "true"],
        )

    def test_old_flow_spelling_is_rejected(self) -> None:
        with self.assertRaises(LexError):
            tokenize("emit [1, 2] |> size()")

    def test_registered_reserved_operator_reports_its_id(self) -> None:
        with self.assertRaisesRegex(ParseError, "RPR_OP_011"):
            parse("1 ::: 2")

    def test_indexing(self) -> None:
        self.assertEqual(self.capture("make xs := [10, 20]\nemit xs[1]"), ["20"])

    def test_division_by_zero_has_location(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "division by zero"):
            self.capture("emit 4 / 0")

    def test_zero_to_negative_power_is_a_language_error(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "numeric operation failed"):
            self.capture("emit 0 ** -1")

    def test_complex_power_result_is_rejected(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "real numbers"):
            self.capture("emit (-1) ** 0.5")

    def test_execution_budget_stops_infinite_loop(self) -> None:
        with self.assertRaises(ExecutionLimitError):
            self.capture("loop while true {\n    emit 1\n}", max_steps=20)

    def test_strict_text_concatenation(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "joins text"):
            self.capture('emit "count=" ++ 5')

    def test_collection_limit_rejects_large_list_literal(self) -> None:
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            interpreter.run("emit [1, 2, 3]")

    def test_collection_limit_rejects_large_range_before_iteration(self) -> None:
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            interpreter.run("each n in range(0, 3) {\n    emit n\n}")

    def test_push_cannot_exceed_collection_limit(self) -> None:
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            interpreter.run("emit [1, 2] :: push(3)")

    def test_text_concatenation_limit(self) -> None:
        interpreter = Interpreter(output=lambda _line: None, max_text_length=4)
        with self.assertRaisesRegex(ReaperRuntimeError, "text length limit"):
            interpreter.run('emit "abc" ++ "de"')

    def test_resource_limits_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            Interpreter(max_collection_items=0)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            Interpreter(max_text_length=0)

    def test_assert_builtin(self) -> None:
        self.assertEqual(
            self.capture('assert(2 + 2 == 4)\nemit "ok"'),
            ["ok"],
        )

    def test_yield_outside_function_is_a_language_error(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "inside a craft"):
            self.capture("yield 1")

    def test_recursive_functions(self) -> None:
        source = """
        craft factorial(n) {
            when n <= 1 {
                yield 1
            }
            yield n * factorial(n - 1)
        }
        emit factorial(6)
        """
        self.assertEqual(self.capture(source), ["720"])

    def test_recursive_call_depth_is_bounded(self) -> None:
        interpreter = Interpreter(
            output=lambda _line: None,
            max_steps=10_000,
            max_call_depth=12,
        )
        with self.assertRaisesRegex(ReaperRuntimeError, "call-depth limit"):
            interpreter.run(
                "craft descend(n) { yield descend(n + 1) }\nemit descend(0)"
            )

    def test_nested_list_equality_is_strict(self) -> None:
        self.assertEqual(
            self.capture("emit [true] == [1]\nemit [1, 2] == [1, 2]"),
            ["false", "true"],
        )

    def test_when_without_otherwise_can_be_followed_by_statement(self) -> None:
        source = 'when false {\n    emit "wrong"\n}\nemit "right"'
        self.assertEqual(self.capture(source), ["right"])


if __name__ == "__main__":
    unittest.main()
