from __future__ import annotations

import json
import unittest

from reaper.ir import lower
from reaper.lexer import tokenize
from reaper.parser import parse


class SourceSpanTests(unittest.TestCase):
    def test_lexer_tracks_unicode_character_and_utf8_byte_ranges(self):
        source = 'emit "ёж"\n'
        tokens = tokenize(source)
        string_token = next(token for token in tokens if token.kind == "STRING")
        span = string_token.span

        self.assertIsNotNone(span)
        assert span is not None
        self.assertEqual(source[span.start:span.end], '"ёж"')
        self.assertEqual(
            source.encode("utf-8")[span.byte_start:span.byte_end].decode("utf-8"),
            '"ёж"',
        )
        self.assertEqual((span.line, span.column), (1, 6))
        self.assertEqual((span.end_line, span.end_column), (1, 10))
        self.assertEqual(span.byte_end - span.byte_start, len('"ёж"'.encode("utf-8")))

    def test_ast_exposes_the_originating_token_span(self):
        source = "make total := 42\n"
        tree = parse(source, "boot.rpr")
        declaration = tree.children[0]

        self.assertEqual(declaration.span, declaration.token.span)
        self.assertEqual(source[declaration.span.start:declaration.span.end], "make")

    def test_lowering_preserves_spans_and_emits_deterministic_source_map(self):
        source = "make total := 1 + 2\n"
        module = lower(parse(source, "kernel.rpr"), "kernel.rpr")

        self.assertTrue(module.code)
        self.assertTrue(all(item.span is not None for item in module.code))
        self.assertTrue(all(item.origin_span == item.span for item in module.code))

        serialized = module.to_json()
        self.assertEqual(serialized, module.to_json())
        document = json.loads(serialized)
        self.assertEqual(document["schema"], "reaper.canonical-ir/v1")
        self.assertEqual(document["source_name"], "kernel.rpr")
        self.assertEqual(len(document["source_map"]), len(module.code))
        self.assertEqual(
            [entry["instruction"] for entry in document["source_map"]],
            list(range(len(module.code))),
        )

    def test_control_flow_patching_does_not_discard_source_spans(self):
        source = "when true {\n    emit 1\n}\n"
        module = lower(parse(source))

        jump = next(item for item in module.code if item.op == "JUMP_IF_FALSE")
        self.assertIsNotNone(jump.span)
        self.assertEqual(jump.origin_span, jump.span)
        self.assertGreaterEqual(jump.argument, 0)

    def test_nested_function_ir_is_serializable_with_its_origin(self):
        source = "craft identity(value) { yield value }\n"
        module = lower(parse(source))
        document = json.loads(module.to_json())
        function = next(item for item in document["code"] if item["op"] == "MAKE_FUNCTION")

        self.assertEqual(function["argument"]["kind"], "function")
        self.assertEqual(function["argument"]["name"], "identity")
        self.assertIsNotNone(function["argument"]["span"])
        self.assertTrue(function["argument"]["code"])

    def test_legacy_tokens_without_spans_remain_supported(self):
        from reaper.lexer import Token

        legacy = Token("IDENT", "answer", 1, 1)
        self.assertIsNone(legacy.span)


if __name__ == "__main__":
    unittest.main()
