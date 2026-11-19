import importlib.util, json, unittest
from pathlib import Path
ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("validate_features", ROOT / "tools" / "validate_features.py")
validator = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(validator)

class FeatureRegistryTests(unittest.TestCase):
    def test_repository_registry_is_valid(self):
        data = json.loads((ROOT / "language" / "features.json").read_text(encoding="utf-8"))
        self.assertEqual(validator.validate(data), 7)
    def test_cycle_is_rejected(self):
        data = {"features":[{"id":"A","status":"planned","depends_on":["B"]},{"id":"B","status":"planned","depends_on":["A"]}]}
        with self.assertRaisesRegex(ValueError, "cycle"): validator.validate(data)
    def test_unknown_dependency_is_rejected(self):
        data = {"features":[{"id":"A","status":"planned","depends_on":["MISSING"]}]}
        with self.assertRaisesRegex(ValueError, "unknown"): validator.validate(data)

if __name__ == "__main__": unittest.main()
