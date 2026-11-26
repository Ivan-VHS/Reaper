from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (Path(__file__).resolve().parents[1] / "frameworks" / "foundation.rpr").resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as foundation\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_has_exactly_five_unique_frameworks(self) -> None:
        self.assertEqual(self.run_expression('size(foundation["foundation_frameworks"]())'), ["5"])
        self.assertEqual(self.run_expression('foundation["foundation_validate_catalog"]()'), ["true"])
        self.assertEqual(
            self.run_expression('foundation["foundation_find_framework"]("architecture.framework-frame.v1")[1]'),
            ["Framework frame"],
        )
        self.assertEqual(self.run_expression('size(foundation["foundation_framework_ids"]())'), ["5"])
        expected_ids = [
            "architecture.framework-frame.v1",
            "architecture.platform.v1",
            "architecture.environment.v1",
            "architecture.infrastructure.v1",
            "architecture.architecture.v1",
        ]
        for index, identifier in enumerate(expected_ids):
            self.assertEqual(
                self.run_expression(f'foundation["foundation_framework_ids"]()[{index}]'),
                [identifier],
            )

    def test_scaffold_requires_all_project_areas(self) -> None:
        self.assertEqual(
            self.run_expression(
                'foundation["foundation_validate_scaffold"](["reaper", "src", "include/reaper", "tests", "docs"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'foundation["foundation_validate_scaffold"](["reaper", "src", "tests"])'
            ),
            ["false"],
        )

    def test_platform_and_environment_maturity_is_enforced(self) -> None:
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_platform"]("hosted-reference")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_platform"]("freestanding")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_environment"]("canonical-vm")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_environment"]("freestanding")'),
            ["false"],
        )

    def test_infrastructure_budget_must_be_six_positive_numbers(self) -> None:
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_budget"]([1000, 32, 1000, 4096, 65536, 8])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_budget"]([1000, 0, 1000, 4096, 65536, 8])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_budget"]([1000, 32, 1000, 4096.5, 65536, 8])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('foundation["foundation_validate_budget"]([1000, 32])'),
            ["false"],
        )

    def test_architecture_pipeline_is_ordered(self) -> None:
        self.assertEqual(
            self.run_expression(
                'foundation["foundation_validate_architecture"](foundation["foundation_architecture_order"]())'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'foundation["foundation_validate_architecture"](["source", "parser", "lexer"])'
            ),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
