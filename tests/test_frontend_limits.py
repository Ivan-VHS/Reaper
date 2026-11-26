from __future__ import annotations

import unittest
from unittest.mock import patch

from reaper.errors import LexError
from reaper.lexer import Lexer, tokenize


class FrontendLimitTests(unittest.TestCase):
    def test_source_length_limit_fails_before_tokenization(self) -> None:
        with patch("reaper.lexer.MAX_SOURCE_CHARS", 8):
            with self.assertRaisesRegex(LexError, "8-character limit"):
                Lexer("make value").tokenize()

    def test_token_count_limit_is_enforced_while_scanning(self) -> None:
        with patch("reaper.lexer.MAX_TOKEN_COUNT", 2):
            with self.assertRaisesRegex(LexError, "token limit"):
                tokenize("make value := 1", "too-many-tokens.rpr")

    def test_normal_source_and_unicode_positions_are_unchanged(self) -> None:
        tokens = tokenize('emit "Привет"\nemit 2', "unicode.rpr")
        self.assertEqual(tokens[0].kind, "EMIT")
        self.assertEqual(tokens[1].kind, "STRING")
        self.assertEqual(tokens[1].value, "Привет")
        self.assertEqual(tokens[-1].kind, "EOF")
        self.assertEqual(tokens[-1].line, 2)


if __name__ == "__main__":
    unittest.main()
