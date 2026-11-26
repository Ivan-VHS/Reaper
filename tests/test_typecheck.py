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


    def test_typed_parameters_and_return_types_are_checked(self):
        valid = check_source("""
        craft add(left: Int, right: Int) -> Int {
            yield left + right
        }
        emit add(20, 22)
        """)
        self.assertTrue(valid.ok, valid.as_dict())

        invalid_argument = check_source("""
        craft add(left: Int, right: Int) -> Int {
            yield left + right
        }
        emit add("twenty", 22)
        """)
        self.assertFalse(invalid_argument.ok)
        self.assertIn("RPR-T0014", [item.code for item in invalid_argument.diagnostics])

    def test_explicit_return_type_is_checked(self):
        result = check_source("""
        craft invalid() -> Int {
            yield "not an integer"
        }
        """)
        self.assertFalse(result.ok)
        self.assertIn("RPR-T0013", [item.code for item in result.diagnostics])

    def test_generic_function_infers_type_arguments(self):
        result = check_source("""
        craft identity<T>(value: T) -> T {
            yield value
        }
        craft twice<T: Numeric>(value: T) -> T {
            yield value * 2
        }
        make answer := identity(42)
        make doubled := twice(answer)
        emit doubled
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_generic_trait_bounds_reject_unsupported_types(self):
        result = check_source("""
        craft twice<T: Numeric>(value: T) -> T {
            yield value * 2
        }
        emit twice("not numeric")
        """)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(item.code in {"RPR-T0014", "RPR-T0015"} for item in result.diagnostics),
            result.as_dict(),
        )

    def test_result_and_option_generic_types_are_checked(self):
        result = check_source("""
        craft parse_count(value: Int) -> Result<Int, Text> {
            when value >= 0 {
                yield ok(value)
            } otherwise {
                yield err("negative")
            }
        }
        craft find_label(value: Text) -> Option<Text> {
            yield some(value)
        }
        make parsed := parse_count(7)
        make label := find_label("ready")
        emit result_is_ok(parsed)
        emit option_is_some(label)
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_result_and_option_type_arity_is_checked(self):
        result = check_source("""
        craft invalid() -> Result<Int> {
            yield ok(1)
        }
        """)
        self.assertFalse(result.ok)
        self.assertIn("RPR-T0017", [item.code for item in result.diagnostics])

    def test_function_effect_contracts_are_enforced(self):
        valid = check_source("""
        craft announce(message: Text) -> Nothing effects(console) {
            say(message)
        }
        craft run() -> Nothing effects(console) {
            announce("ready")
        }
        """)
        self.assertTrue(valid.ok, valid.as_dict())

        invalid = check_source("""
        craft announce(message: Text) -> Nothing effects(console) {
            say(message)
        }
        craft run() -> Nothing effects() {
            announce("ready")
        }
        """)
        self.assertFalse(invalid.ok)
        self.assertIn("RPR-EFF0002", [item.code for item in invalid.diagnostics])

    def test_unknown_effect_names_are_rejected(self):
        result = check_source("""
        craft run() -> Nothing effects(telepathy) {
            yield nothing
        }
        """)
        self.assertFalse(result.ok)
        self.assertIn("RPR-EFF0001", [item.code for item in result.diagnostics])

    def test_reference_types_are_preserved_in_signature_metadata(self):
        from reaper.parser import parse

        tree = parse("craft borrow(value: &Item) -> &Item { yield value }")
        signature = tree.children[0].metadata
        self.assertEqual(signature["parameter_types"], ("&Item",))
        self.assertEqual(signature["return_type"], "&Item")

    def test_allows_text_keys_on_unknown_map_like_host_values(self):
        result = check_source("""
        make report := read_json("report.json")
        emit report["schema"]
        """)
        self.assertTrue(result.ok, result.as_dict())

    def test_rejects_indexing_a_scalar_value(self):
        result = check_source("""
        make count := 42
        emit count[0]
        """)
        self.assertFalse(result.ok)
        self.assertEqual(result.diagnostics[0].code, "RPR-T0008")

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
