from __future__ import annotations

import unittest

from reaper.composition import compose, concat, concat_text, merge_mappings, pipe


class SequenceConcatenationTests(unittest.TestCase):
    def test_concat_preserves_order_and_does_not_mutate_inputs(self) -> None:
        left = [1, 2]
        right = (3, 4)
        self.assertEqual(concat(left, right), (1, 2, 3, 4))
        self.assertEqual(left, [1, 2])

    def test_concat_empty_parts_and_limit(self) -> None:
        self.assertEqual(concat(), ())
        self.assertEqual(concat([1, 2], max_items=2), (1, 2))
        with self.assertRaisesRegex(ValueError, "max_items"):
            concat([1], [2], max_items=1)

    def test_concat_rejects_invalid_limit_and_non_iterable(self) -> None:
        with self.assertRaises(TypeError):
            concat([1], max_items=True)
        with self.assertRaises(TypeError):
            concat(42)  # type: ignore[arg-type]


class TextConcatenationTests(unittest.TestCase):
    def test_text_join_and_separator(self) -> None:
        self.assertEqual(concat_text("Harlem", "Metal", separator=" "), "Harlem Metal")
        self.assertEqual(concat_text(), "")

    def test_text_limit_and_types(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_length"):
            concat_text("abc", "def", max_length=5)
        with self.assertRaises(TypeError):
            concat_text("a", 2)  # type: ignore[arg-type]


class MappingCompositionTests(unittest.TestCase):
    def test_explicit_conflict_policies(self) -> None:
        first = {"a": 1, "b": 2}
        second = {"b": 9, "c": 3}
        self.assertEqual(merge_mappings(first, second, on_conflict="first"),
                         {"a": 1, "b": 2, "c": 3})
        self.assertEqual(merge_mappings(first, second, on_conflict="last"),
                         {"a": 1, "b": 9, "c": 3})
        with self.assertRaisesRegex(ValueError, "conflict"):
            merge_mappings(first, second)

    def test_mapping_limits_and_invalid_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_keys"):
            merge_mappings({"a": 1, "b": 2}, max_keys=1)
        with self.assertRaises(ValueError):
            merge_mappings({}, on_conflict="silent")

    def test_function_composition_and_pipeline_order(self) -> None:
        double = lambda value: value * 2
        add_three = lambda value: value + 3
        self.assertEqual(compose(double, add_three)(4), 14)
        self.assertEqual(pipe(4, add_three, double), 14)
        self.assertEqual(compose()(9), 9)
        self.assertEqual(pipe(9), 9)

    def test_function_members_must_be_callable(self) -> None:
        with self.assertRaises(TypeError):
            compose(lambda value: value, 7)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            pipe(1, None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
