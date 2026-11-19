import unittest

from reaper.errors import ReaperRuntimeError
from reaper.runtime import Interpreter


class ConcatenationTests(unittest.TestCase):
    def evaluate(self, source: str, **limits):
        interpreter = Interpreter(output=lambda _text: None, **limits)
        interpreter.run(source)
        return interpreter.globals

    def test_concat_joins_text_without_coercion(self):
        globals_ = self.evaluate('make result := concat("Re", "ap", "er")')
        self.assertEqual(globals_.get("result"), "Reaper")

    def test_concat_joins_sequences_in_order(self):
        globals_ = self.evaluate("make result := concat([1, 2], [3], range(4, 6))")
        self.assertEqual(globals_.get("result"), [1, 2, 3, 4, 5])

    def test_concat_empty_input_is_empty_text(self):
        globals_ = self.evaluate("make result := concat()")
        self.assertEqual(globals_.get("result"), "")

    def test_join_uses_explicit_separator(self):
        globals_ = self.evaluate('make result := join(" / ", ["alpha", "beta", "gamma"])')
        self.assertEqual(globals_.get("result"), "alpha / beta / gamma")

    def test_extend_flattens_one_sequence_level(self):
        globals_ = self.evaluate("make result := extend([1, 2], [3, 4])")
        self.assertEqual(globals_.get("result"), [1, 2, 3, 4])

    def test_concat_operator_supports_sequences(self):
        globals_ = self.evaluate("make result := [1, 2] ++ [3, 4]")
        self.assertEqual(globals_.get("result"), [1, 2, 3, 4])

    def test_concat_rejects_mixed_types(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "only text values or only sequences"):
            self.evaluate('make result := concat("text", [1])')

    def test_concat_enforces_text_limit(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "text length limit"):
            self.evaluate('make result := concat("123", "456")', max_text_length=5)

    def test_concat_enforces_collection_limit(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            self.evaluate("make result := concat([1, 2], [3])", max_collection_items=2)

    def test_join_rejects_non_text_items(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "only text values"):
            self.evaluate('make result := join(",", ["ok", 2])')


if __name__ == "__main__":
    unittest.main()
