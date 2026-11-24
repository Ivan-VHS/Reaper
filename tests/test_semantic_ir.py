from __future__ import annotations

import unittest

from reaper.lexer import tokenize
from reaper.parser import parse
from reaper.source import LineIndex
from reaper.semantic_ir import (
    FunctionSignature,
    IRCall,
    analyze_expression_source,
    IRIntrinsic,
    IRTypeChecker,
    IRVar,
    lower_expression,
    verify_semantic_ir,
)


class SemanticIRTests(unittest.TestCase):
    def test_multiline_arrow_pipeline_lowers_with_piped_value_first(self) -> None:
        source = (
            "make result := raw_lines\n"
            "    -> parse_codes()\n"
            "    -> sum_counts()\n"
            "    -> filter_5xx()"
        )
        module = lower_expression(parse(source, "pipeline.rpr"), "pipeline.rpr")
        verify_semantic_ir(module)

        outer = module.root
        self.assertIsInstance(outer, IRCall)
        self.assertTrue(outer.from_pipe)
        self.assertIsInstance(outer.callee, IRVar)
        self.assertEqual(outer.callee.name, "filter_5xx")
        self.assertEqual(len(outer.arguments), 1)

        previous = outer.arguments[0]
        self.assertIsInstance(previous, IRCall)
        self.assertTrue(previous.from_pipe)
        self.assertIsInstance(previous.callee, IRVar)
        self.assertEqual(previous.callee.name, "sum_counts")
        self.assertIsInstance(previous.arguments[0], IRCall)
        self.assertEqual(previous.arguments[0].callee.name, "parse_codes")
        self.assertEqual(previous.arguments[0].arguments[0].name, "raw_lines")

    def test_pipe_lowering_preserves_pipe_and_stage_source_provenance(self) -> None:
        source = "make result := items\n  -> transform()"
        module = lower_expression(parse(source, "origin.rpr"), "origin.rpr")
        call = module.root
        self.assertIsInstance(call, IRCall)
        self.assertEqual(call.span.source_id, "origin.rpr")
        self.assertEqual(call.span.line, 2)
        self.assertEqual(call.span.column, 6)
        self.assertEqual(call.origin.transformation, "pipe-lowering")
        self.assertEqual(len(call.origin.related), 2)
        pipe_span = call.origin.related[0]
        self.assertEqual((pipe_span.line, pipe_span.column), (2, 3))

    def test_operator_expressions_become_named_intrinsic_calls(self) -> None:
        module = lower_expression(parse("emit status >= 500", "compare.rpr"), "compare.rpr")
        self.assertIsInstance(module.root, IRCall)
        self.assertIsInstance(module.root.callee, IRIntrinsic)
        self.assertEqual(module.root.callee.name, "ge")

    def test_type_error_points_to_the_failing_pipeline_stage(self) -> None:
        source = (
            "make result := raw_lines\n"
            "    -> parse_codes()\n"
            "    -> sum_counts()\n"
            "    -> filter_5xx()"
        )
        module = lower_expression(parse(source, "pipeline.rpr"), "pipeline.rpr")
        signatures = {
            "parse_codes": FunctionSignature(("List[Text]",), "List[Int]"),
            "sum_counts": FunctionSignature(("List[Int]",), "Int"),
            "filter_5xx": FunctionSignature(("List[Int]",), "List[Int]"),
        }
        result = IRTypeChecker(
            variables={"raw_lines": "List[Text]"},
            functions=signatures,
        ).check(module)

        self.assertFalse(result.ok)
        diagnostic = result.diagnostics[0]
        self.assertEqual(diagnostic.code, "RPR-I0002")
        self.assertIn("filter_5xx", diagnostic.message)
        self.assertEqual((diagnostic.span.line, diagnostic.span.column), (4, 8))
        rendered = diagnostic.format(source)
        self.assertIn("pipeline.rpr:4:8", rendered)
        self.assertIn("ir_node: IRCall", rendered)
        self.assertIn("^^^^^^^^^^", rendered)

    def test_valid_map_callback_contract(self) -> None:
        source = "make doubled := [1, 2, 3] -> map(double)"
        module = lower_expression(parse(source, "map.rpr"), "map.rpr")
        result = IRTypeChecker(
            functions={"double": FunctionSignature(("Int",), "Int")}
        ).check(module)
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(result.return_type, "List[Int]")
        self.assertEqual(result.typed_module.root.inferred_type, "List[Int]")
        self.assertEqual(result.typed_module.root.callee.inferred_type, "Function")
        self.assertEqual(result.typed_module.root.arguments[0].inferred_type, "List[Int]")

    def test_arrow_is_an_alias_for_existing_double_colon_pipe(self) -> None:
        arrow = lower_expression(parse("emit values -> size()", "arrow.rpr"), "arrow.rpr")
        legacy = lower_expression(parse("emit values :: size()", "legacy.rpr"), "legacy.rpr")
        self.assertIsInstance(arrow.root, IRCall)
        self.assertIsInstance(legacy.root, IRCall)
        self.assertTrue(arrow.root.from_pipe)
        self.assertTrue(legacy.root.from_pipe)
        self.assertEqual(arrow.root.callee.name, legacy.root.callee.name)
        self.assertEqual(len(arrow.root.arguments), len(legacy.root.arguments))

    def test_comparison_type_mismatch_uses_operator_span(self) -> None:
        source = 'emit code >= "500"'
        analysis = analyze_expression_source(
            source,
            "compare.rpr",
            variables={"code": "Int"},
        )
        self.assertFalse(analysis.ok)
        diagnostic = analysis.type_check.diagnostics[0]
        self.assertEqual(diagnostic.code, "RPR-I0002")
        self.assertEqual((diagnostic.span.line, diagnostic.span.column), (1, 11))
        rendered = diagnostic.format(source)
        self.assertIn("operator 'ge' cannot compare Int with Text", rendered)
        self.assertIn("ir_node: IRCall", rendered)

    def test_line_index_handles_crlf_and_trailing_newlines(self) -> None:
        source = "one\r\ntwo\n"
        index = LineIndex(source)
        self.assertEqual(index.line_text(1), "one")
        self.assertEqual(index.line_text(2), "two")
        self.assertEqual(index.line_text(3), "")
        self.assertEqual(index.byte_position(len("one\r\n".encode("utf-8"))), (2, 1))
        self.assertEqual(index.byte_position(len(source.encode("utf-8"))), (3, 1))

    def test_crlf_newlines_keep_byte_and_line_coordinates_consistent(self) -> None:
        source = "make value := 1\r\nemit value"
        tokens = tokenize(source, "windows.rpr")
        emit = next(token for token in tokens if token.value == "emit")
        self.assertEqual((emit.line, emit.column), (2, 1))
        self.assertEqual(emit.start_byte, len("make value := 1\r\n".encode("utf-8")))

    def test_utf8_byte_offsets_are_not_confused_with_character_columns(self) -> None:
        source = "# комментарий\nmake result := raw_lines -> missing_stage()"
        tokens = tokenize(source, "unicode.rpr")
        stage = next(token for token in tokens if token.value == "missing_stage")
        expected = len(source[: source.index("missing_stage")].encode("utf-8"))
        self.assertEqual(stage.start_byte, expected)
        self.assertEqual(stage.line, 2)
        self.assertEqual(stage.column, 29)
        self.assertEqual(stage.span.source_id, "unicode.rpr")


if __name__ == "__main__":
    unittest.main()
