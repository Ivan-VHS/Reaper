"""Tests for deterministic and bounded Reaper Studio editor services."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from reaper.ide_support import highlight_spans, iter_project_entries


class HighlightTests(unittest.TestCase):
    def test_highlights_keywords_strings_numbers_and_comments(self) -> None:
        source = 'make count := 42\nemit "make 99" // yield 12\n'
        spans = highlight_spans(source)
        values = [(span.kind, source[span.start:span.end]) for span in spans]
        self.assertIn(("keyword", "make"), values)
        self.assertIn(("number", "42"), values)
        self.assertIn(("keyword", "emit"), values)
        self.assertIn(("string", '"make 99"'), values)
        self.assertIn(("comment", "// yield 12"), values)
        self.assertNotIn(("keyword", "yield"), values)

    def test_russian_keywords_and_unicode_identifiers(self) -> None:
        source = "пусть значение := 7"
        spans = highlight_spans(source)
        self.assertEqual(source[spans[0].start:spans[0].end], "пусть")
        self.assertEqual(spans[0].kind, "keyword")
        self.assertNotIn("значение", [source[s.start:s.end] for s in spans])

    def test_spans_are_ordered_and_do_not_overlap(self) -> None:
        source = 'make x := "value" // note'
        spans = highlight_spans(source)
        self.assertEqual(list(spans), sorted(spans, key=lambda item: item.start))
        for left, right in zip(spans, spans[1:]):
            self.assertLessEqual(left.end, right.start)


class ProjectTreeTests(unittest.TestCase):
    def test_tree_is_deterministic_and_filters_non_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "z.rpr").write_text("emit 1", encoding="utf-8")
            (root / "a.txt").write_text("ignored", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "main.most").write_text("вывести 2", encoding="utf-8")
            (root / "build").mkdir()
            (root / "build" / "generated.rpr").write_text("ignored", encoding="utf-8")
            entries = list(iter_project_entries(root))
            self.assertEqual([entry.path.name for entry in entries], ["src", "main.most", "z.rpr"])
            self.assertEqual([entry.depth for entry in entries], [1, 2, 1])

    def test_tree_respects_depth_and_entry_limits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "one" / "two").mkdir()
            (root / "one" / "two" / "file.rpr").write_text("emit 1", encoding="utf-8")
            self.assertEqual(len(list(iter_project_entries(root, max_depth=1))), 1)
            self.assertEqual(len(list(iter_project_entries(root, max_entries=1))), 1)

    def test_invalid_limits_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            list(iter_project_entries(Path("."), max_depth=-1))
        with self.assertRaises(ValueError):
            list(iter_project_entries(Path("."), max_entries=0))


if __name__ == "__main__":
    unittest.main()
