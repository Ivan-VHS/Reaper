from __future__ import annotations

import unittest

from reaper.ir import lower
from reaper.lexer import tokenize
from reaper.parser import Parser


class SourceSpanTests(unittest.TestCase):
    def test_lexer_tracks_utf8_byte_ranges(self) -> None:
        source = 'вывести "утка"\nвывести 42'
        tokens = tokenize(source, "unicode.rpr")
        string_token = next(token for token in tokens if token.kind == "STRING")
        number_token = next(token for token in tokens if token.kind == "NUMBER")

        self.assertEqual(string_token.source_name, "unicode.rpr")
        self.assertEqual(
            source.encode("utf-8")[string_token.start_offset:string_token.end_offset],
            '"утка"'.encode("utf-8"),
        )
        expected_number_start = len('вывести "утка"\nвывести '.encode("utf-8"))
        self.assertEqual(number_token.start_offset, expected_number_start)
        self.assertEqual(number_token.end_offset, expected_number_start + 2)
        self.assertEqual(number_token.line, 2)
        self.assertEqual(number_token.column, 9)
        self.assertEqual(number_token.span.to_dict()["file"], "unicode.rpr")

    def test_canonical_ir_retains_instruction_source_map(self) -> None:
        source = 'emit "утка"\nemit 42'
        filename = "sample.rpr"
        tree = Parser(tokenize(source, filename), filename).parse()
        module = lower(tree)

        self.assertEqual(module.source_name, filename)
        self.assertTrue(module.source_map)
        for entry in module.source_map:
            self.assertEqual(entry.span.source_name, filename)
            self.assertLessEqual(entry.span.start_offset, entry.span.end_offset)
            self.assertLessEqual(entry.span.end_offset, len(source.encode("utf-8")))
        numeric = next(
            entry for entry in module.source_map
            if source.encode("utf-8")[entry.span.start_offset:entry.span.end_offset] == b"42"
        )
        self.assertGreaterEqual(numeric.instruction_index, 0)


if __name__ == "__main__":
    unittest.main()
