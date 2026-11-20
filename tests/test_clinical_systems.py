import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "clinical_systems.py"
SPEC = importlib.util.spec_from_file_location("clinical_systems", MODULE)
csr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(csr)

class ClinicalSystemsTests(unittest.TestCase):
    def test_registry_has_120_unique_ids(self):
        self.assertEqual(len(csr.CATALOG), 120)
        self.assertEqual(len({x["id"] for x in csr.CATALOG}), 120)

    def test_healthy_empty_metrics(self):
        self.assertEqual(csr.assess({"metrics": {}})["status"], "healthy")

    def test_detects_critical_resource_failure(self):
        result = csr.assess({"metrics": {"available_memory_ratio": 0.02}})
        self.assertEqual(result["status"], "critical")
        self.assertEqual(result["findings"][0]["principle"], "CSR-035")

    def test_threshold_override(self):
        result = csr.assess({"metrics": {"cpu_utilization": 0.8},
                             "thresholds": {"cpu_utilization": 0.7}})
        self.assertEqual(result["status"], "critical")

    def test_rejects_non_finite_metric(self):
        result = csr.assess({"metrics": {"cpu_utilization": float("nan")}})
        self.assertEqual(result["status"], "critical")
        self.assertEqual(result["findings"][0]["severity"], "invalid")

if __name__ == "__main__":
    unittest.main()
