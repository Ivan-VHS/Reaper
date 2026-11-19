import unittest

from tools.most_plan import build_plan


def registry():
    return {
        "schema": "most.feature-registry/v1",
        "language": "MOST",
        "edition": "test",
        "features": [
            {"id": "A", "name": "module syntax", "area": "syntax", "status": "verified", "depends_on": [], "acceptance": []},
            {"id": "B", "name": "function syntax", "area": "syntax", "status": "specified", "depends_on": ["A"], "acceptance": ["parser"]},
            {"id": "C", "name": "integer types", "area": "types", "status": "planned", "depends_on": ["B"], "acceptance": ["typecheck"]},
            {"id": "D", "name": "independent formatter", "area": "tools", "status": "planned", "depends_on": [], "acceptance": ["format"]},
        ],
    }


class MostPlanTests(unittest.TestCase):
    def test_topological_order_and_readiness(self):
        plan = build_plan(registry())
        self.assertEqual(plan["selected"], ["A", "B", "C", "D"])
        self.assertEqual(plan["work_order"], ["B", "C", "D"])
        self.assertEqual(plan["ready"], ["B", "D"])
        self.assertEqual(plan["blocked"], ["C"])
        self.assertEqual(plan["items"][1]["blocked_by"], ["B"])

    def test_target_includes_transitive_dependencies_only(self):
        plan = build_plan(registry(), ["C"])
        self.assertEqual(plan["selected"], ["A", "B", "C"])
        self.assertEqual(plan["work_order"], ["B", "C"])

    def test_multiple_targets_are_deduplicated(self):
        plan = build_plan(registry(), ["C", "B"])
        self.assertEqual(plan["selected"], ["A", "B", "C"])
        self.assertEqual(plan["summary"]["selected"], 3)

    def test_unknown_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown target"):
            build_plan(registry(), ["MISSING"])

    def test_invalid_dependency_graph_is_rejected(self):
        data = registry()
        data["features"][1]["depends_on"] = ["NO_SUCH_FEATURE"]
        with self.assertRaisesRegex(ValueError, "unknown"):
            build_plan(data)

    def test_completed_targets_need_no_work(self):
        plan = build_plan(registry(), ["A"])
        self.assertEqual(plan["work_order"], [])
        self.assertEqual(plan["summary"]["completed"], 1)


if __name__ == "__main__":
    unittest.main()
