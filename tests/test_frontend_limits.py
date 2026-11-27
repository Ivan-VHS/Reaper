from __future__ import annotations

import unittest
from unittest.mock import patch

from reaper.errors import LexError, ParseError
from reaper.lexer import Lexer, tokenize
from reaper.parser import parse


class FrontendLimitTests(unittest.TestCase):
    def test_source_length_limit_fails_before_tokenization(self) -> None:
        with patch("reaper.lexer.MAX_SOURCE_CHARS", 8):
            with self.assertRaisesRegex(LexError, "8-character limit"):
                Lexer("make value").tokenize()

    def test_token_count_limit_is_enforced_while_scanning(self) -> None:
        with patch("reaper.lexer.MAX_TOKEN_COUNT", 2):
            with self.assertRaisesRegex(LexError, "token limit"):
                tokenize("make value := 1", "too-many-tokens.rpr")

    def test_utf8_byte_budget_is_independent_of_character_budget(self) -> None:
        with patch("reaper.lexer.MAX_SOURCE_CHARS", 100):
            with patch("reaper.lexer.MAX_SOURCE_BYTES", 3):
                with self.assertRaisesRegex(LexError, "3-byte UTF-8 limit"):
                    Lexer("éé", "multibyte.rpr").tokenize()

    def test_rejects_embedded_nul_with_source_location(self) -> None:
        with self.assertRaisesRegex(LexError, r"NUL.*2:2"):
            Lexer("a\nb\0c", "nul.rpr").tokenize()

    def test_rejects_unpaired_surrogates_before_tokenization(self) -> None:
        with self.assertRaisesRegex(LexError, "invalid Unicode surrogate"):
            Lexer("emit \ud800", "surrogate.rpr").tokenize()

    def test_expression_nesting_limit_prevents_python_recursion_failure(self) -> None:
        source = "(" * 300 + "1" + ")" * 300
        with self.assertRaisesRegex(ParseError, "expression nesting limit"):
            parse(source, "deep-expression.rpr")

    def test_block_nesting_limit_prevents_python_recursion_failure(self) -> None:
        depth = 140
        source = "when true {\n" * depth + "emit 1\n" + "}\n" * depth
        with self.assertRaisesRegex(ParseError, "block nesting limit"):
            parse(source, "deep-blocks.rpr")

    def test_identifier_limit_is_enforced_during_lexing(self) -> None:
        with patch("reaper.lexer.MAX_IDENTIFIER_CHARS", 4):
            with self.assertRaisesRegex(LexError, "identifier exceeds the 4-character limit"):
                Lexer("abcdef", "long-name.rpr").tokenize()

    def test_numeric_literal_limit_is_enforced_during_lexing(self) -> None:
        with patch("reaper.lexer.MAX_NUMERIC_LITERAL_CHARS", 4):
            with self.assertRaisesRegex(LexError, "numeric literal exceeds the 4-character limit"):
                Lexer("12345", "long-number.rpr").tokenize()

    def test_normal_source_and_unicode_positions_are_unchanged(self) -> None:
        tokens = tokenize('emit "Привет"\nemit 2', "unicode.rpr")
        self.assertEqual(tokens[0].kind, "EMIT")
        self.assertEqual(tokens[1].kind, "STRING")
        self.assertEqual(tokens[1].value, "Привет")
        self.assertEqual(tokens[-1].kind, "EOF")
        self.assertEqual(tokens[-1].line, 2)


if __name__ == "__main__":
    unittest.main()
