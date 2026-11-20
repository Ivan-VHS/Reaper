from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO

from reaper.atlas import ARCHITECTURES, LANGUAGES, format_atlas, search_atlas, validate_atlas
from reaper.cli import main


class SystemsAtlasTests(unittest.TestCase):
    def test_registry_contains_66_unique_languages_and_architectures(self) -> None:
        validate_atlas()
        self.assertEqual(len(LANGUAGES), 66)
        self.assertEqual(len({item.name.casefold() for item in LANGUAGES}), 66)
        self.assertGreaterEqual(len(ARCHITECTURES), 12)

    def test_search_finds_memory_and_verification_models(self) -> None:
        self.assertEqual([item.name for item in search_atlas("Vale", "languages")], ["Vale"])
        self.assertIn("SPARK", [item.name for item in search_atlas("formal contracts", "languages")])
        self.assertIn("riscv64", [item.name for item in search_atlas("RISC-V", "architectures")])

    def test_search_validates_queries_and_kinds(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            search_atlas("  ")
        with self.assertRaisesRegex(ValueError, "kind"):
            search_atlas("Odin", "drivers")

    def test_format_contains_all_profiles_and_caveat(self) -> None:
        output = format_atlas("all")
        self.assertIn("66 language profiles", output)
        self.assertIn("14 architecture profiles", output)
        self.assertIn("do not imply an installed compiler", output)

    def test_cli_can_list_architectures_without_source_file(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            result = main(["--atlas", "--atlas-kind", "architectures"])
        self.assertEqual(result, 0)
        self.assertIn("Reaper systems atlas", output.getvalue())
        self.assertIn("riscv64", output.getvalue())


if __name__ == "__main__":
    unittest.main()
