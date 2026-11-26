from __future__ import annotations

import json
from pathlib import Path
import unittest

from reaper import Interpreter


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "reaper" / "frameworks" / "framework-index.v1.json"
RUNNER = ROOT / "tests" / "_framework_runner.rpr"


def load_index() -> dict:
    return json.loads(INDEX.read_text(encoding="utf-8"))


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
        cls.index = load_index()
        cls.frameworks = cls.index["frameworks"]

    def test_index_covers_all_sixty_five_domains_and_325_frameworks(self) -> None:
        self.assertEqual(self.index["schema"], "reaper.framework-index/v1")
        self.assertEqual(self.index["target_framework_count"], 325)
        self.assertEqual(len(self.index["domains"]), 65)
        self.assertEqual(len(self.frameworks), 325)
        self.assertEqual(len({item["id"] for item in self.frameworks}), 325)
        self.assertEqual(len({item["path"] for item in self.frameworks}), 325)

    def test_every_framework_has_an_independent_reaper_module(self) -> None:
        missing = [item["path"] for item in self.frameworks if not (ROOT / item["path"]).is_file()]
        self.assertEqual(missing, [])

    def test_every_framework_accepts_its_valid_contract_fixture(self) -> None:
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

    def test_every_framework_rejects_or_reports_its_negative_contract_fixture(self) -> None:
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
