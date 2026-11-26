from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrameworkFederationRegistryTests(unittest.TestCase):
    def test_registry_matches_all_reaper_source_handlers(self) -> None:
        manifest = json.loads(
            (ROOT / "language" / "frameworks.v1.json").read_text(encoding="utf-8")
        )
        schema = json.loads(
            (ROOT / "schemas" / "reaper-framework-registry.v1.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(manifest["version"], "1.1.0")
        self.assertEqual(schema["properties"]["version"]["const"], "1.1.0")
        self.assertEqual(manifest["registry"]["framework_count"], 20)
        self.assertEqual(manifest["registry"]["function_contract_count"], 120)
        self.assertEqual(manifest["registry"]["reference_runtime_handlers"], 120)
        self.assertEqual(manifest["public_statistics"]["reaper_reference_handlers"], 120)
        self.assertEqual(manifest["public_statistics"]["executable_domain_handlers"], 0)
        self.assertEqual(manifest["public_statistics"]["reaper_source_bindings"], 0)

        seen_frameworks: set[str] = set()
        seen_function_keys: set[str] = set()
        source_handler_count = 0

        for framework in manifest["frameworks"]:
            framework_id = framework["id"]
            self.assertNotIn(framework_id, seen_frameworks)
            seen_frameworks.add(framework_id)
            self.assertEqual(framework["maturity"], "reference-handler-v1-partial")
            self.assertEqual(len(framework["functions"]), 6)

            source_path = ROOT / framework["source_module"]
            self.assertTrue(source_path.is_file(), str(source_path))
            source = source_path.read_text(encoding="utf-8")

            self.assertIn(
                'export make handler_status := "reference-source-handler-v1"',
                source,
                framework_id,
            )

            for operation in framework["functions"]:
                key = operation["key"]
                self.assertNotIn(key, seen_function_keys)
                seen_function_keys.add(key)
                self.assertEqual(operation["status"], "reference-source-handler-v1")
                pattern = r"export\s+craft\s+" + re.escape(operation["name"]) + r"\s*\("
                self.assertRegex(source, pattern, f"{framework_id}.{operation['name']}")
                source_handler_count += 1

        self.assertEqual(len(seen_frameworks), 20)
        self.assertEqual(len(seen_function_keys), 120)
        self.assertEqual(source_handler_count, 120)


if __name__ == "__main__":
    unittest.main()
