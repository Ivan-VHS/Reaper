from __future__ import annotations

import json
from pathlib import Path
import unittest

from reaper import Interpreter


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "reaper" / "frameworks" / "framework-index.v1.json"
RUNNER = ROOT / "tests" / "_framework_runner.rpr"
SKELETON_ROOT = ROOT / "reaper" / "frameworks" / "skeleton"


def run_framework(entry: dict, args: str) -> list[str]:
    relative = Path(entry["path"]).relative_to("reaper")
    specifier = f"../reaper/{relative.as_posix()}"
    source = (
        f'import "{specifier}" as framework\n'
        f'emit framework["{entry["api"]}"]{args}\n'
    )
    output: list[str] = []
    Interpreter(output=output.append).run(source, filename=str(RUNNER))
    return output


class FrameworkProgrammeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.frameworks = cls.index["frameworks"]

    def test_programme_counts_and_domain_slots_are_consistent(self) -> None:
        self.assertEqual(self.index["schema"], "reaper.framework-index/v1")
        self.assertEqual(self.index["total_target_framework_count"], 330)
        self.assertEqual(self.index["remaining_target_framework_count"], 0)
        self.assertEqual(self.index["existing_batch_01_source_count"], 5)
        self.assertEqual(self.index["new_source_count"], 325)
        self.assertEqual(self.index["remaining_source_count"], 0)
        self.assertEqual(len(self.index["domains"]), 66)
        self.assertEqual(sum(domain["framework_slots"] for domain in self.index["domains"]), 330)
        self.assertEqual(len(self.frameworks), 325)
        self.assertEqual(len({item["id"] for item in self.frameworks}), 325)
        self.assertEqual(len({item["path"] for item in self.frameworks}), 325)
        self.assertEqual({item["domain_number"] for item in self.frameworks}, set(range(2, 67)))
        for domain in self.index["domains"]:
            with self.subTest(domain=domain["number"]):
                self.assertEqual(domain["source_frameworks"], 5)

    def test_every_framework_is_an_independent_reaper_module(self) -> None:
        missing = [item["path"] for item in self.frameworks if not (ROOT / item["path"]).is_file()]
        self.assertEqual(missing, [])

    def test_first_batch_skeleton_modules_are_present(self) -> None:
        expected = {"manifest.rpr", "layers.rpr", "lifecycle.rpr", "capabilities.rpr", "extensions.rpr"}
        actual = {path.name for path in SKELETON_ROOT.glob("*.rpr")}
        self.assertTrue(expected.issubset(actual))

    def test_each_framework_accepts_its_valid_contract(self) -> None:
        failures = []
        for entry in self.frameworks:
            with self.subTest(framework=entry["id"]):
                try:
                    output = run_framework(entry, entry["positive"]["args"])
                except Exception as error:
                    failures.append(f'{entry["id"]}: {type(error).__name__}: {error}')
                    continue
                if output != [entry["positive"]["output"]]:
                    failures.append(
                        f'{entry["id"]}: expected {entry["positive"]["output"]!r}, got {output!r}'
                    )
        self.assertEqual(failures, [])

    def test_additional_edge_fixtures(self) -> None:
        for entry in self.frameworks:
            for args, expected in entry.get("additional_positive", []):
                with self.subTest(framework=entry["id"], args=args):
                    self.assertEqual(run_framework(entry, args), [expected])
            for args, expected in entry.get("additional_negative", []):
                with self.subTest(framework=entry["id"], args=args):
                    self.assertEqual(run_framework(entry, args), [expected])

    def test_each_framework_rejects_its_invalid_contract(self) -> None:
        failures = []
        for entry in self.frameworks:
            with self.subTest(framework=entry["id"]):
                try:
                    output = run_framework(entry, entry["negative"]["args"])
                except Exception as error:
                    failures.append(f'{entry["id"]}: {type(error).__name__}: {error}')
                    continue
                if output != [entry["negative"]["output"]]:
                    failures.append(
                        f'{entry["id"]}: expected {entry["negative"]["output"]!r}, got {output!r}'
                    )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
