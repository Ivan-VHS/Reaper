from __future__ import annotations

import json
from pathlib import Path
import unittest

from reaper.runtime import Interpreter


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_PATH = ROOT / "frameworks" / "portfolio.v1.json"
PORTFOLIO_SCHEMA_PATH = ROOT / "schemas" / "framework-portfolio.v1.schema.json"
EXPECTED_NEW_MODULES = {
    "Vorke",
    "Jellymeat",
    "LejjyFish",
    "Lejjy",
    "Oplos",
    "Holmosaptimu",
    "Sentan",
    "Cellene",
    "Kolir",
    "SOMO",
}


class FrameworkPortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.portfolio = json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))

    def test_portfolio_matches_its_versioned_json_schema(self) -> None:
        schema = json.loads(PORTFOLIO_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema"]["const"], "reaper.framework-portfolio.v1")
        self.assertIn("integration_surfaces", schema["required"])
        self.assertTrue((ROOT / "examples" / "frameworks_portfolio_smoke.rpr").is_file())

    def test_portfolio_counts_all_sixty_owned_modules(self) -> None:
        modules = [
            item
            for group in self.portfolio["groups"]
            for item in group["items"]
        ]
        self.assertEqual(len(modules), 60)
        self.assertEqual(
            len({item["id"] for item in modules}),
            len(modules),
        )
        self.assertEqual(self.portfolio["scale_policy"]["counted_modules"], 60)
        self.assertEqual(
            self.portfolio["scale_policy"]["total_qualified_production_reaper_loc_target"],
            3_000_000,
        )

    def test_ten_requested_modules_have_reaper_sources(self) -> None:
        standalone = next(
            group
            for group in self.portfolio["groups"]
            if group["id"] == "standalone"
        )
        new_modules = [
            item for item in standalone["items"]
            if item["name"] in EXPECTED_NEW_MODULES
        ]
        self.assertEqual({item["name"] for item in new_modules}, EXPECTED_NEW_MODULES)
        for item in new_modules:
            with self.subTest(module=item["name"]):
                self.assertTrue(item["source"])
                self.assertTrue((ROOT / item["source"]).is_file())
                self.assertEqual(item["implementation_language"], "Reaper")

    def test_existing_framework_surfaces_remain_discoverable(self) -> None:
        surfaces = {
            item["id"]: item
            for item in self.portfolio["integration_surfaces"]
        }
        self.assertEqual(len(surfaces), len(self.portfolio["integration_surfaces"]))
        self.assertEqual(len(surfaces["rforge"]["members"]), 20)
        self.assertTrue(all(
            member["counted_in_core_60"] is False
            and member["status"] == "source_present_runtime_validation_pending"
            for member in surfaces["rforge"]["members"]
        ))
        for required in (
            "framework-federation-registry",
            "framework-federation-handlers",
            "native-framework-core",
            "rforge",
            "rivet",
            "plague",
            "kora",
            "internal-products",
            "native-capability-suite",
            "system-runtime-abi",
            "dabi64",
            "jora",
            "self-hosting",
            "most-qcs",
        ):
            with self.subTest(surface=required):
                self.assertIn(required, surfaces)

    def test_all_portfolio_source_paths_exist_when_declared(self) -> None:
        for group in self.portfolio["groups"]:
            for item in group["items"]:
                source = item.get("source")
                if source:
                    with self.subTest(module=item["id"]):
                        self.assertTrue((ROOT / source).is_file())

    def test_ten_framework_smoke_program_runs(self) -> None:
        source_path = ROOT / "examples" / "frameworks_portfolio_smoke.rpr"
        output: list[str] = []
        Interpreter(output=output.append).run(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )
        self.assertEqual(output, ["ten framework smoke checks passed"])


if __name__ == "__main__":
    unittest.main()
