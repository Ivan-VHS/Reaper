from __future__ import annotations

import unittest

from reaper.typecheck import check_source


class StaticTypeCheckerTests(unittest.TestCase):
    def test_accepts_numeric_expressions_and_inferred_lists(self):
        result = check_source("""
        make subtotal := 40 + 2
        make values := [1, 2, 3]
        emit subtotal
        emit values[0]
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_rejects_text_as_a_numeric_operand(self):
        result = check_source('make invalid := "forty" * 2')
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0004")

    def test_rejects_text_concatenation_with_a_number(self):
        result = check_source('emit "count: " ++ 3')
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0005")

    def test_detects_reassignment_of_immutable_binding(self):
        result = check_source("""
        make answer := 42
        change answer := 43
        """)
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0002")

    def test_rejects_mutable_reassignment_to_an_incompatible_type(self):
        result = check_source("""
        vary count := 3
        change count := "three"
        """)
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0001")

    def test_allows_safe_integer_to_float_widening(self):
        result = check_source("""
        vary ratio := 1.5
        change ratio := 2
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_checks_user_function_arity(self):
        result = check_source("""
        craft add(left, right) { yield left + right }
        emit add(1)
        """)
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0007")

    def test_checks_index_type(self):
        result = check_source("""
        make values := [10, 20]
        emit values["first"]
        """)
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0003")

    def test_recognizes_collection_pipeline(self):
        result = check_source("""
        craft double(value) { yield value * 2 }
        make values := [1, 2, 3] :: map(double)
        emit values
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_reports_non_iterable_values(self):
        result = check_source("""
        each item in 42 {
            emit item
        }
        """)
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0008")


if __name__ == "__main__":
    unittest.main()
