import importlib.util, json, unittest
from pathlib import Path
ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("validate_most_matrix", ROOT / "tools" / "validate_most_matrix.py")
validator = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(validator)

class MostCombinatorialMatrixTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "language" / "most_matrix_20x20.json").read_text(encoding="utf-8"))
    def clone(self):
        return json.loads(json.dumps(self.data))
    def test_repository_matrix_has_all_400_directed_pairs(self):
        self.assertEqual(validator.validate(self.data), 400)
    def test_missing_projection_is_rejected(self):
        data=self.clone(); data["projections"].pop()
        with self.assertRaisesRegex(ValueError, "exactly 400"): validator.validate(data)
    def test_duplicate_pair_is_rejected(self):
        data=self.clone(); data["projections"][1]["column_id"]="E01"; data["projections"][1]["id"]="MOST-M20-01-01"
        with self.assertRaisesRegex(ValueError, "duplicate"): validator.validate(data)
    def test_unknown_basis_reference_is_rejected(self):
        data=self.clone(); data["projections"][0]["column_id"]="E21"
        with self.assertRaisesRegex(ValueError, "unknown basis"): validator.validate(data)
    def test_action_drift_is_rejected(self):
        data=self.clone(); data["projections"][0]["target_action"]="другое действие"
        with self.assertRaisesRegex(ValueError, "target_action"): validator.validate(data)
    def test_projected_entries_do_not_claim_execution(self):
        data=self.clone(); data["projections"][0]["execution_claim"]=True
        with self.assertRaisesRegex(ValueError, "specified"): validator.validate(data)

if __name__ == "__main__": unittest.main()
