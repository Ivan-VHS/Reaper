import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = json.loads(
    (ROOT / "federation" / "ecosystem-cloud-adapter.v1.json").read_text(encoding="utf-8")
)


class EcosystemCloudAdapterContractTests(unittest.TestCase):
    def test_contract_identity_and_shared_version(self):
        self.assertEqual(ADAPTER["schema"], "ivan-vhs.ecosystem-cloud-adapter.v1")
        self.assertEqual(ADAPTER["version"], 1)
        self.assertEqual(ADAPTER["project"], "reaper")
        self.assertEqual(ADAPTER["project_key"], "reaper")
        self.assertEqual(ADAPTER["shared_contract"], "ivan-vhs.ecosystem-cloud.v1")
        self.assertEqual(ADAPTER["shared_contract_version"], 1)
        self.assertEqual(ADAPTER["status"], "contract-only")

    def test_local_first_and_explicit_opt_in(self):
        runtime = ADAPTER["runtime"]
        self.assertEqual(runtime["default_network_mode"], "disabled")
        self.assertTrue(runtime["user_opt_in_required"])
        self.assertFalse(runtime["core_requires_network"])
        self.assertEqual(runtime["supabase_transport"], "not-implemented")
        self.assertFalse(ADAPTER["compatibility"]["sdk_dependency"])

    def test_private_source_and_credentials_are_never_publishable(self):
        denied = set(ADAPTER["denylist"])
        self.assertIn("private-source-trees", denied)
        self.assertIn("access-tokens", denied)
        self.assertIn("service-role-keys", denied)
        self.assertIn("local-build-outputs", denied)
        self.assertTrue(ADAPTER["synchronization"]["local_source_of_truth"])
        self.assertTrue(ADAPTER["synchronization"]["upload_requires_user_action"])


if __name__ == "__main__":
    unittest.main()
