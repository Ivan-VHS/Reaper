import unittest

from reaper.products import (
    ProductError, get_product, inspect_value, list_products, plan_workflow,
    run_product, verify_evidence,
)


class ProductRegistryTests(unittest.TestCase):
    def test_all_eighteen_products_are_unique(self):
        products = list_products()
        self.assertEqual(len(products), 18)
        self.assertEqual(len({item["name"].casefold() for item in products}), 18)

    def test_dropaul_is_canonical_workflow_product_name(self):
        self.assertEqual(get_product("Dropaul").name, "Dropaul")
        with self.assertRaises(ProductError):
            get_product("Patakee")

    def test_legacy_workflow_names_are_not_aliases(self):
        for legacy_name in ("Pataki", "Patakee", "Doopraul"):
            with self.assertRaises(ProductError):
                get_product(legacy_name)

    def test_operandu_rejects_non_finite_numbers(self):
        with self.assertRaisesRegex(ProductError, "non-finite"):
            inspect_value(float("nan"))

    def test_dropaul_workflow_is_deterministic_and_dry_run(self):
        result = run_product("Dropaul", "plan_workflow", steps=[
            {"id": "compile", "depends_on": []},
            {"id": "test", "depends_on": ["compile"]},
            {"id": "package", "depends_on": ["test"]},
        ])
        self.assertEqual(result["execution_order"], ["compile", "test", "package"])
        self.assertTrue(result["dry_run"])

    def test_workflow_rejects_cycles_and_unknown_dependencies(self):
        with self.assertRaisesRegex(ProductError, "cycle"):
            plan_workflow([{"id": "a", "depends_on": ["b"]}, {"id": "b", "depends_on": ["a"]}])
        with self.assertRaisesRegex(ProductError, "unknown"):
            plan_workflow([{"id": "a", "depends_on": ["missing"]}])

    def test_operandu_rejects_unsupported_objects(self):
        with self.assertRaises(ProductError):
            inspect_value(object())

    def test_vprossee_reports_missing_evidence(self):
        report = verify_evidence([{"id": "REQ-1", "evidence": []}, {"id": "REQ-2", "evidence": ["test-output"]}])
        self.assertFalse(report["complete"])
        self.assertEqual(report["verified"], 1)


if __name__ == "__main__":
    unittest.main()
