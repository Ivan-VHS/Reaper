from __future__ import annotations

import unittest

from reaper.formatter import format_document


class FormatterTests(unittest.TestCase):
    def test_normalizes_indentation_and_trailing_whitespace(self):
        source = "craft greet(name) {\n emit name   \n}\n"
        self.assertEqual(format_document(source), "craft greet(name) {\n    emit name\n}\n")

    def test_ignores_braces_inside_strings(self):
        source = 'craft show() {\n emit "{"\n}\n'
        self.assertEqual(format_document(source), 'craft show() {\n    emit "{"\n}\n')

    def test_preserves_blank_lines_and_adds_final_newline(self):
        self.assertEqual(format_document("craft run() {\n\n emit 1\n}"), "craft run() {\n\n    emit 1\n}\n")

    def test_rejects_invalid_width_and_oversized_documents(self):
        with self.assertRaises(ValueError):
            format_document("emit 1", indent_width=0)
        with self.assertRaises(ValueError):
            format_document("x" * (2 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
