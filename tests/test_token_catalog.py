from __future__ import annotations
import unittest
from reaper import Interpreter
from reaper.lexer import tokenize
from reaper.token_catalog import CATALOG_GROUPS, TOKEN_ALPHABET, TOKEN_CATALOG_SIZE, catalog_summary, token_catalog, token_info, token_is_reserved, validate_token_catalog

class TokenCatalogTests(unittest.TestCase):
    def test_unique_digit_free_lexemes(self):
        validate_token_catalog()
        entries = token_catalog()
        self.assertEqual(len(entries), 666)
        lexemes = [entry["lexeme"] for entry in entries]
        self.assertEqual(len(set(lexemes)), 666)
        for lexeme in lexemes:
            self.assertEqual(len(lexeme), 3)
            self.assertTrue(set(lexeme) <= set(TOKEN_ALPHABET))
            self.assertFalse(any(char.isdigit() for char in lexeme))

    def test_six_domain_sizes(self):
        self.assertEqual(CATALOG_GROUPS, ("memory", "flow", "types", "arithmetic", "metrics", "diagnostics"))
        self.assertEqual([len(token_catalog(group)) for group in CATALOG_GROUPS], [120, 120, 120, 120, 100, 86])
        self.assertEqual(catalog_summary()["entry_count"], TOKEN_CATALOG_SIZE)

    def test_lexer_recognizes_first_and_last_tokens(self):
        for lexeme in (token_catalog()[0]["lexeme"], token_catalog()[-1]["lexeme"]):
            token = tokenize(lexeme)[0]
            self.assertEqual((token.kind, token.value), ("CATALOG_OPERATOR", lexeme))
            self.assertTrue(token_is_reserved(lexeme))
        self.assertEqual(token_info(":::")["ordinal"], 1)
        self.assertEqual(token_info("}}}")["ordinal"], 666)

    def test_catalog_introspection_inside_reaper(self):
        output = []
        Interpreter(output=output.append).run('emit token_is_reserved(":::")\nemit size(token_catalog())')
        self.assertEqual(output, ["true", "666"])

    def test_reserved_operators_are_not_mistaken_for_implemented_operators(self):
        from reaper import ParseError
        with self.assertRaisesRegex(ParseError, "reserved"):
            Interpreter(output=lambda _: None).run("emit 1 ::: 2")

    def test_bad_group_and_bad_lookup_types(self):
        with self.assertRaises(ValueError):
            token_catalog("unknown")
        with self.assertRaises(TypeError):
            token_info(42)

if __name__ == "__main__":
    unittest.main()
