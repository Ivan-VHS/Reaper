from __future__ import annotations

import unittest

from reaper.ast_diff import ast_to_data, compare_sources, diff_data
from reaper.parser import parse


class AstDiffTests(unittest.TestCase):
    def test_formatting_and_comment_changes_are_ignored(self):
        before = "make answer := 40 + 2\nemit answer"
        after = "# a harmless note\nmake answer:=40+2\n\nemit answer"
        report = compare_sources(before, after)
        self.assertTrue(report["equal"])
        self.assertEqual(report["change_count"], 0)

    def test_russian_and_english_keyword_aliases_share_semantics(self):
        report = compare_sources("пусть count := 3\nвывести count", "make count := 3\nemit count")
        self.assertTrue(report["equal"])

    def test_literal_and_operator_changes_are_reported(self):
        report = compare_sources("make count := 3 + 4", "make count := 3 * 4")
        self.assertFalse(report["equal"])
        self.assertGreaterEqual(report["change_count"], 1)
        paths = [change["path"] for change in report["changes"]]
        self.assertTrue(any(path.endswith(".value") for path in paths))

    def test_locations_are_optional(self):
        compact = ast_to_data(parse("make value := 1"))
        with_locations = ast_to_data(parse("\nmake value := 1"), include_locations=True)
        self.assertNotIn("location", compact)
        self.assertIn("location", with_locations["children"][0])
        self.assertFalse(compare_sources("make value := 1", "\nmake value := 1")["equal"] is False)

    def test_diff_handles_added_and_removed_nodes(self):
        changes = diff_data({"items": [1, 2]}, {"items": [1, 2, 3]})
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["change"], "added")
        self.assertEqual(changes[0]["path"], "$.items[2]")


if __name__ == "__main__":
    unittest.main()
