from __future__ import annotations

import unittest

from reaper import Interpreter, LexError, ParseError
from reaper.lexer import tokenize
from reaper.diagnostic_catalog import diagnose_exception
from reaper.parser import parse
from reaper.ir import lower
from reaper.source_profile import SourceProfileError, span_for_node, span_for_token
from reaper.typecheck import check_source


class MixedSourceProfileTests(unittest.TestCase):
    def capture(self, source: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source, "mixed.rpr")
        return output

    def test_indented_bare_flow_step_executes(self) -> None:
        source = """@use mode=flow locale=ru
make итог := [1, 2, 3]
    -> sum
emit итог
"""
        self.assertEqual(self.capture(source), ["6"])

    def test_inline_arrow_and_gutter_pipe_are_flow_aliases(self) -> None:
        source = """@mode flow
emit [1, 2, 3] |> sum()
emit [4, 5] -> sum()
"""
        self.assertEqual(self.capture(source), ["6", "9"])

    def test_flow_chains_match_between_treewalk_and_vm(self) -> None:
        source = (
            "@mode flow\n"
            "craft double(value) { yield value * 2 }\n"
            "make total := [1, 2, 3]\n"
            "  -> map(double)\n"
            "  |> sum\n"
            "emit total"
        )
        outputs = {}
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(source, "mixed-flow.rpr", engine=engine)
            outputs[engine] = output
        self.assertEqual(outputs["treewalk"], ["12"])
        self.assertEqual(outputs["vm"], outputs["treewalk"])

    def test_bare_flow_step_is_checked_as_an_injected_argument(self) -> None:
        result = check_source("""@use mode=flow locale=en
make total := [1, 2, 3]
  -> sum
""")
        self.assertTrue(result.ok, result.as_dict())

    def test_classic_default_remains_compatible_and_rejects_new_aliases(self) -> None:
        tokens = tokenize("emit [1, 2] :: size()")
        self.assertIn("::", [token.kind for token in tokens])
        with self.assertRaises(LexError):
            tokenize("emit [1, 2] |> size()")
        with self.assertRaises(LexError):
            tokenize("@mode classic\nemit [1, 2] -> size()")

    def test_multiple_modes_and_locales_can_coexist_in_one_file(self) -> None:
        source = """@use mode=flow locale=ru
make первое := [1, 2]
  -> sum
@use mode=classic locale=uk
нехай друге := sum([3, 4])
@use mode=flow locale=most
make третье := [5, 6]
  -> sum
вывести первое
@use locale=uk
вивести друге
@use locale=most
emit третье
"""
        self.assertEqual(self.capture(source), ["3", "7", "11"])

        tokens = tokenize(source, "mixed.rpr")
        pipe_tokens = [token for token in tokens if token.kind == "PIPE"]
        self.assertEqual([token.locale for token in pipe_tokens], ["ru", "most"])
        self.assertEqual([token.syntax_mode for token in pipe_tokens], ["flow", "flow"])

    def test_short_mode_and_locale_directives(self) -> None:
        source = """@mode flow
@locale uk
вивести [2, 3]
  |> sum
"""
        self.assertEqual(self.capture(source), ["5"])

    def test_ukrainian_keywords_are_exact_aliases(self) -> None:
        self.assertEqual(
            self.capture("""@locale uk
нехай число := 5
вивести число
"""),
            ["5"],
        )
        self.assertEqual(
            [token.kind for token in tokenize("структура структурою")],
            ["STRUCT", "IDENT", "EOF"],
        )
        self.assertEqual(
            [token.kind for token in tokenize("у і")],
            ["IDENT", "IDENT", "EOF"],
        )
        self.assertEqual(
            [
                token.kind
                for token in tokenize("@locale uk\nу і")
                if token.kind != "NEWLINE"
            ],
            ["IN", "AND", "EOF"],
        )

    def test_span_is_half_open_and_uses_original_source_offsets(self) -> None:
        source = "@use mode=flow locale=ru\nmake xs := [1, 2]\n  |> sum\n"
        token = next(item for item in tokenize(source, "span.rpr") if item.kind == "PIPE")
        span = span_for_token(token, "span.rpr")
        expected = source.index("|>")
        self.assertEqual(
            (span.file, span.line, span.col, span.start, span.end),
            ("span.rpr", 3, 3, expected, expected + 2),
        )

    def test_ast_expression_span_covers_the_full_flow_expression(self) -> None:
        source = "@use mode=flow locale=ru\nmake xs := [1, 2]\n  |> sum\n"
        tree = parse(source, "ast-span.rpr")
        statement = tree.children[0]
        span = span_for_node(statement, "ast-span.rpr")
        self.assertEqual(
            (span.file, span.line, span.col, span.start, span.end),
            (
                "ast-span.rpr",
                2,
                1,
                source.index("make"),
                source.index("sum") + len("sum"),
            ),
        )

    def test_canonical_ir_keeps_span_mode_and_locale(self) -> None:
        source = "@use mode=flow locale=ru\nmake xs := [1, 2]\n  -> sum\n"
        module = lower(parse(source, "ir-span.rpr"), "ir-span.rpr")
        instruction = next(item for item in module.code if item.op == "PIPE_CALL")
        self.assertEqual(instruction.syntax_mode, "flow")
        self.assertEqual(instruction.locale, "ru")
        self.assertIsNotNone(instruction.span)
        self.assertEqual(instruction.span.file, "ir-span.rpr")
        self.assertEqual(source[instruction.span.start:instruction.span.end], "[1, 2]\n  -> sum")

    def test_semantic_diagnostic_uses_active_locale_and_has_a_span(self) -> None:
        russian_source = '@locale ru\nmake invalid := "x" * 2'
        russian = check_source(russian_source, "type-ru.rpr")
        self.assertFalse(russian.ok)
        diagnostic = russian.diagnostics[0]
        self.assertIn("требует числовые операнды", diagnostic.message)
        self.assertIsNotNone(diagnostic.span)
        self.assertEqual(diagnostic.span.file, "type-ru.rpr")
        self.assertEqual(diagnostic.syntax_mode, "classic")
        self.assertEqual(diagnostic.locale, "ru")
        start = russian_source.index('"x"')
        end = russian_source.index("2", start) + 1
        self.assertEqual(
            russian_source[diagnostic.span.start:diagnostic.span.end],
            russian_source[start:end],
        )

        ukrainian = check_source('@locale uk\nemit "x" ++ 2')
        self.assertFalse(ukrainian.ok)
        self.assertIn("потребує операнди Text", ukrainian.diagnostics[0].message)

    def test_lexer_diagnostic_has_locale_and_exact_span(self) -> None:
        source = "@locale uk\nemit \"bad\\q\""
        with self.assertRaises(LexError) as caught:
            tokenize(source, "lex-uk.rpr")
        error = caught.exception
        self.assertEqual(error.locale, "uk")
        self.assertEqual(error.syntax_mode, "classic")
        self.assertEqual((error.span.file, error.span.line, error.span.col), ("lex-uk.rpr", 2, 10))
        self.assertIn("невідома escape-послідовність", str(error))

        structured = diagnose_exception(error)
        self.assertEqual(
            structured.range,
            {
                "start": {"line": 1, "character": 9},
                "end": {"line": 1, "character": 11},
            },
        )

    def test_invalid_directive_has_localized_error_and_exact_span(self) -> None:
        source = "@locale ru\n@mode experimental\n"
        with self.assertRaises(SourceProfileError) as caught:
            tokenize(source, "directive.rpr")
        error = caught.exception
        self.assertEqual(error.locale, "ru")
        self.assertEqual(error.syntax_mode, "classic")
        self.assertEqual((error.span.line, error.span.col), (2, 1))
        self.assertIn("неподдерживаемый режим", str(error))

    def test_parser_diagnostic_uses_active_locale(self) -> None:
        with self.assertRaises(ParseError) as caught:
            parse("@locale uk\nemit )", "uk-error.rpr")
        error = caught.exception
        self.assertIn("очікувався вираз", str(error))
        self.assertIn("uk-error.rpr:2:6", str(error))
        self.assertEqual((error.span.line, error.span.col), (2, 6))
        self.assertEqual((error.syntax_mode, error.locale), ("classic", "uk"))


if __name__ == "__main__":
    unittest.main()
