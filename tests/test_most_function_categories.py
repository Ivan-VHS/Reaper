import copy
import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_most_functions",
    ROOT / "tools" / "validate_most_functions.py",
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class MostFunctionCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(
            (ROOT / "language" / "function_registry.v1.json").read_text(encoding="utf-8")
        )

    def test_registry_has_expected_categorized_entry_count(self):
        count, _, _ = validator.validate(self.data)
        self.assertEqual(count, 666)
        self.assertEqual(len(self.data["functions"]), 666)
        self.assertTrue(all(item.get("architecture_category") for item in self.data["functions"]))

    def test_category_counts_cover_all_entries(self):
        actual = Counter(item["architecture_category"] for item in self.data["functions"])
        declared = {
            category["id"]: category["count"]
            for category in self.data["architecture_categories"]
        }
        self.assertEqual(actual, declared)
        self.assertEqual(sum(declared.values()), 666)

    def test_original_registry_groups_remain_unchanged_and_covered(self):
        mapped = {
            group_id
            for category in self.data["architecture_categories"]
            for group_id in category["source_groups"]
        }
        self.assertEqual(mapped, {group["id"] for group in self.data["groups"]})

    def test_unknown_category_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["functions"][0]["architecture_category"] = "missing-category"
        with self.assertRaisesRegex(ValueError, "unknown architecture category"):
            validator.validate(data)

    def test_category_mismatch_with_original_group_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["functions"][0]["architecture_category"] = "desktop-ui"
        with self.assertRaisesRegex(ValueError, "wrong architecture category"):
            validator.validate(data)

    def test_incorrect_category_total_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["architecture_categories"][0]["count"] += 1
        with self.assertRaisesRegex(ValueError, "wrong category count"):
            validator.validate(data)

    def test_unassigned_original_group_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["architecture_categories"][0]["source_groups"].remove("MOST-MEM-BASE")
        with self.assertRaisesRegex(ValueError, "category/group mapping mismatch"):
            validator.validate(data)


if __name__ == "__main__":
    unittest.main()
