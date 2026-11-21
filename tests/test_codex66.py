import json
import unittest

from reaper.codex66 import (
    CATEGORIES, FEATURES, STATUS_LABELS, export_json,
    search_features, status_counts, validate_catalog,
)


class Codex66CatalogueTests(unittest.TestCase):
    def test_catalogue_has_66_ordered_unique_entries(self):
        self.assertEqual(validate_catalog(), 66)
        self.assertEqual([item.id for item in FEATURES], [f"{i:02d}" for i in range(1, 67)])

    def test_six_categories_have_eleven_entries_each(self):
        counts = {key: sum(item.category == key for item in FEATURES) for key, _ in CATEGORIES}
        self.assertEqual(len(counts), 6)
        self.assertEqual(set(counts.values()), {11})

    def test_status_vocabulary_is_explicit(self):
        counts = status_counts()
        self.assertEqual(set(counts), set(STATUS_LABELS))
        self.assertEqual(sum(counts.values()), 66)
        self.assertGreater(counts["implemented"], 0)
        self.assertGreater(counts["planned"], 0)
        self.assertGreater(counts["not_supported"], 0)

    def test_search_filters_by_text_category_and_status(self):
        found = search_features("IntelliSense")
        self.assertEqual([item.id for item in found], ["02"])
        editor = search_features(category="editor-nav")
        self.assertEqual(len(editor), 11)
        planned = search_features(status="planned")
        self.assertTrue(planned)
        self.assertTrue(all(item.status == "planned" for item in planned))
        self.assertEqual(search_features("no-such-feature"), ())

    def test_export_is_versioned_and_does_not_claim_a_sandbox(self):
        payload = json.loads(export_json())
        self.assertEqual(payload["schema"], "reaper.codex66.v1")
        self.assertEqual(payload["catalogue_count"], 66)
        self.assertEqual(len(payload["features"]), 66)
        self.assertIn("Catalogue metadata only", payload["notice"])
        by_id = {item["id"]: item for item in payload["features"]}
        self.assertEqual(by_id["60"]["status"], "not_supported")


if __name__ == "__main__":
    unittest.main()
