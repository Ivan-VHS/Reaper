from __future__ import annotations

import unittest

from reaper import ExecutionLimitError, Interpreter, LexError, ParseError, ReaperRuntimeError
from reaper.lexer import tokenize
from reaper.parser import parse


class LexerTests(unittest.TestCase):
    def test_russian_keyword_aliases(self) -> None:
        tokens = tokenize("""пусть число := истина
переменная сумма := 0
если не ложь и число { вывести сумма }""")
        self.assertEqual(
            [token.kind for token in tokens[:15]],
            ["MAKE", "IDENT", ":=", "TRUE", "NEWLINE", "VARY", "IDENT", ":=", "NUMBER", "NEWLINE", "WHEN", "NOT", "FALSE", "AND", "IDENT"],
        )

    def test_extended_russian_keywords_are_reserved_and_exact(self) -> None:
        aliases = [
            ("попытка", "attempt"),
            ("обработать", "recover"),
            ("наконец", "finally"),
            ("бросить", "throw"),
            ("модуль", "module"),
            ("публичный", "pub"),
            ("процедура", "fn"),
            ("структура", "struct"),
            ("перечисление", "enum"),
            ("типаж", "trait"),
            ("реализация", "impl"),
            ("тип", "type"),
            ("константа", "const"),
            ("связать", "let"),
            ("изменяемый", "mut"),
            ("возврат", "return"),
            ("условие", "if"),
            ("альтернатива", "else"),
            ("выбор", "match"),
            ("область", "region"),
            ("сырой", "raw"),
            ("арена", "arena"),
            ("сигнал", "signal"),
            ("асинхронно", "async"),
            ("ожидать", "await"),
            ("тест", "test"),
            ("вычислить_при_сборке", "comptime"),
            ("требует", "requires"),
            ("гарантирует", "ensures"),
            ("небезопасно", "unsafe"),
            ("внешний", "extern"),
            ("где", "where"),
            ("уничтожить", "drop"),
            ("для_каждого", "for"),
            ("прервать", "break"),
            ("продолжить", "continue"),
            ("отложить", "defer"),
        ]
        words = [alias for alias, _canonical in aliases]
        expected = [canonical.upper() for _alias, canonical in aliases]
        tokens = tokenize(" ".join(words))
        self.assertEqual([token.kind for token in tokens[:-1]], expected)
        self.assertEqual([token.value for token in tokens[:-1]], words)

        # No stemming or automatic case/inflection guessing is performed.
        unknown = tokenize("структуры модулем")
        self.assertEqual([token.kind for token in unknown], ["IDENT", "IDENT", "EOF"])

    def test_reserved_native_vocabulary_has_no_false_runtime_claim(self) -> None:
        # These words are lexed as reserved tokens, but declaration grammar is
        # still acceptance-gated in the native compiler track.
        tokens = tokenize("модуль структура асинхронно вычислить_при_сборке")
        self.assertEqual([token.kind for token in tokens[:-1]], ["MODULE", "STRUCT", "ASYNC", "COMPTIME"])

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


class ParserTests(unittest.TestCase):
    def test_malformed_declaration_has_location(self) -> None:
        with self.assertRaisesRegex(ParseError, r"<memory>:1:"):
            parse("make x = 2")

    def test_attempt_requires_recover_or_finally(self) -> None:
        with self.assertRaisesRegex(ParseError, "needs a 'recover' or 'finally'"):
            parse('attempt { emit "body" }')


class RuntimeTests(unittest.TestCase):
    def capture(self, source: str, max_steps: int = 100_000) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, max_steps=max_steps).run(source)
        return output


    def test_russian_program_subset_executes(self) -> None:
        source = """
        функция удвоить(значение) {
            вернуть значение * 2
        }
        пусть значение := 5
        переменная итог := 0
        для элемент в range(1, 4) {
            изменить итог := итог + удвоить(элемент)
        }
        если итог == 12 {
            вывести "готово"
        } иначе {
            вывести "ошибка"
        }
        """
        self.assertEqual(self.capture(source), ["готово"])

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

    def test_attempt_recover_finally_match_both_engines(self) -> None:
        source = """
        attempt {
            emit 10 / 0
        } recover failure {
            emit contains(failure, "division by zero")
        } finally {
            emit "cleanup"
        }
        """
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["true", "cleanup"], engine)

    def test_attempt_success_skips_recover_and_runs_finally(self) -> None:
        source = """
        attempt {
            emit "body"
        } recover failure {
            emit "wrong"
        } finally {
            emit "done"
        }
        """
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["body", "done"], engine)

    def test_attempt_finally_runs_when_error_is_not_recovered(self) -> None:
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            interpreter = Interpreter(output=output.append)
            with self.assertRaisesRegex(ReaperRuntimeError, "division by zero"):
                interpreter.run(
                    'attempt { emit 1 / 0 } finally { emit "cleanup" }',
                    engine=engine,
                )
            self.assertEqual(output, ["cleanup"], engine)

    def test_attempt_cannot_recover_execution_budget_error(self) -> None:
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            interpreter = Interpreter(output=output.append, max_steps=25)
            source = """
            attempt {
                loop while true { emit "tick" }
            } recover failure {
                emit "caught"
            }
            """
            with self.assertRaises(ExecutionLimitError):
                interpreter.run(source, engine=engine)
            self.assertNotIn("caught", output, engine)

    def test_attempt_finally_runs_before_function_return_in_both_engines(self) -> None:
        source = """
        craft answer() {
            attempt {
                yield 42
            } recover failure {
                yield -1
            } finally {
                emit "closed"
            }
        }
        emit answer()
        """
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["closed", "42"], engine)

    def test_russian_attempt_recover_finally_aliases_execute(self) -> None:
        source = """
        попытка { бросить "сбой" }
        обработать ошибка { вывести contains(ошибка, "thrown: сбой") }
        наконец { вывести "закрыто" }
        """
        self.assertEqual(self.capture(source), ["true", "закрыто"])

    def test_throw_is_recoverable_in_both_engines(self) -> None:
        source = """
        attempt { throw "manual failure" }
        recover failure { emit contains(failure, "thrown: manual failure") }
        """
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, engine=engine)
            self.assertEqual(output, ["true"], engine)

    def test_throw_requires_a_value(self) -> None:
        with self.assertRaisesRegex(ParseError, "expected a value after 'throw'"):
            parse("throw")

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

    def test_indexing(self) -> None:
        self.assertEqual(self.capture("make xs := [10, 20]\nemit xs[1]"), ["20"])

    def test_division_by_zero_has_location(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "division by zero"):
            self.capture("emit 4 / 0")

    def test_euclidean_division_for_all_sign_combinations(self) -> None:
        self.assertEqual(
            self.capture(
                "emit divmod_euclidean(-7, 3)\n"
                "emit divmod_euclidean(7, -3)\n"
                "emit divmod_euclidean(-7, -3)"
            ),
            ["[-3, 2]", "[-2, 1]", "[3, 2]"],
        )

    def test_division_helpers_and_exactness(self) -> None:
        self.assertEqual(
            self.capture(
                "emit quotient(-17, 5)\n"
                "emit remainder(-17, 5)\n"
                "emit is_divisible(42, 7)\n"
                "emit is_divisible(43, 7)"
            ),
            ["-4", "3", "true", "false"],
        )

    def test_division_helpers_reject_zero_and_non_integer_inputs(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "division by zero"):
            self.capture("emit remainder(5, 0)")
        with self.assertRaisesRegex(ReaperRuntimeError, "whole number"):
            self.capture("emit quotient(5.5, 2)")
        with self.assertRaisesRegex(ReaperRuntimeError, "whole number"):
            self.capture("emit quotient(true, 2)")

    def test_balanced_partition_and_existing_text_split(self) -> None:
        self.assertEqual(
            self.capture(
                "emit partition([1, 2, 3, 4, 5, 6, 7], 3)\n"
                'emit partition("abcdef", 4)\n'
                'emit split("a,b", ",")'
            ),
            [
                "[[1, 2, 3], [4, 5], [6, 7]]",
                "[ab, cd, e, f]",
                "[a, b]",
            ],
        )

    def test_equal_and_proportional_distribution(self) -> None:
        self.assertEqual(
            self.capture(
                "emit distribute(10, 3)\n"
                "emit distribute(-7, 3)\n"
                "emit proportional_split(10, [1, 2, 3])"
            ),
            ["[4, 3, 3]", "[-2, -2, -3]", "[2, 3, 5]"],
        )

    def test_distribution_limits_and_invalid_weights(self) -> None:
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            interpreter.run("emit partition([1, 2], 3)")
        with self.assertRaisesRegex(ReaperRuntimeError, "positive"):
            self.capture("emit distribute(10, 0)")
        with self.assertRaisesRegex(ReaperRuntimeError, "positive"):
            self.capture("emit proportional_split(10, [0, 0])")
        with self.assertRaisesRegex(ReaperRuntimeError, "non-negative"):
            self.capture("emit proportional_split(10, [1, -1])")

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
