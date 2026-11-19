import unittest

from reaper.errors import ReaperRuntimeError
from reaper.runtime import Interpreter


class ConcatenationTests(unittest.TestCase):
    def evaluate(self, source: str, **limits):
        return Interpreter(output=lambda _text: None, **limits).run(source)

    def test_concat_joins_text_without_coercion(self):
        self.assertEqual(self.evaluate('emit concat("Re", "ap", "er")'), None)
        self.assertEqual(self.evaluate('make result := concat("Re", "ap", "er")\nemit result'), None)

    def test_concat_joins_sequences_in_order(self):
        interpreter = Interpreter(output=lambda _text: None)
        interpreter.run("make result := concat([1, 2], [3], range(4, 6))")
        self.assertEqual(interpreter.globals.get("result"), [1, 2, 3, 4, 5])

    def test_join_uses_explicit_separator(self):
        interpreter = Interpreter(output=lambda _text: None)
        interpreter.run('make result := join(" / ", ["alpha", "beta", "gamma"])')
        self.assertEqual(interpreter.globals.get("result"), "alpha / beta / gamma")

    def test_extend_flattens_one_sequence_level(self):
        interpreter = Interpreter(output=lambda _text: None)
        interpreter.run("make result := extend([1, 2], [3, 4])")
        self.assertEqual(interpreter.globals.get("result"), [1, 2, 3, 4])

    def test_concat_operator_supports_sequences(self):
        interpreter = Interpreter(output=lambda _text: None)
        interpreter.run("make result := [1, 2] ++ [3, 4]")
        self.assertEqual(interpreter.globals.get("result"), [1, 2, 3, 4])

    def test_concat_rejects_mixed_types(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "only text values or only sequences"):
            self.evaluate('concat("text", [1])')

    def test_concat_enforces_text_limit(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "text length limit"):
            self.evaluate('concat("123", "456")', max_text_length=5)

    def test_concat_enforces_collection_limit(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "collection item limit"):
            self.evaluate("concat([1, 2], [3])", max_collection_items=2)

    def test_join_rejects_non_text_items(self):
        with self.assertRaisesRegex(ReaperRuntimeError, "only text values"):
            self.evaluate('join(",", ["ok", 2])')


if __name__ == "__main__":
    unittest.main()
