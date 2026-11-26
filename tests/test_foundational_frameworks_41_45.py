from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksFortyOneToFortyFiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_41_45.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as engineering\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_forty_five_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('engineering["foundation_validate_catalog_45"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(engineering["foundation_all_frameworks_45"]())'),
            ["45"],
        )
        self.assertEqual(
            self.run_expression('engineering["foundation_all_frameworks_45"]()[44][1]'),
            ["Module"],
        )

    def test_methodology_plan_and_evidence_gates(self) -> None:
        self.assertEqual(
            self.run_expression(
                'engineering["methodology_validate_plan"](["inventory", "specify", "design", "implement", "verify"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["methodology_validate_plan"](["inventory", "implement", "design", "verify"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["methodology_validate_gate"](["verify", ["tests/test_language.py", "CI:python"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["methodology_validate_gate"](["verify", []])'
            ),
            ["false"],
        )

    def test_approach_profiles_are_known_and_unique(self) -> None:
        self.assertEqual(
            self.run_expression(
                'engineering["approach_validate_selection"](["compatibility-first", "evidence-driven"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["approach_validate_selection"](["compatibility-first", "unknown"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["approach_validate_selection"](["local-first", "local-first"])'
            ),
            ["false"],
        )

    def test_system_manifest_and_subsystem_flow(self) -> None:
        self.assertEqual(
            self.run_expression(
                'engineering["system_validate_manifest"](["reaper.system.v1", 1, ["language", "runtime", "tests"], ["reaper.foundation.v1"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["system_validate_manifest"](["reaper.system.v1", 2, ["language"], []])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["subsystem_validate_flow"](["lexer", "parser"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["subsystem_validate_flow"](["lexer", "runtime"])'
            ),
            ["false"],
        )

    def test_module_contracts_and_dependency_graphs(self) -> None:
        first = '["app.math", "math.rpr", 1, 0, ["double"], [], ["pure"]]'
        second = '["app.main", "main.rpr", 1, 0, ["run"], ["app.math"], ["console"]]'
        self.assertEqual(
            self.run_expression(f'engineering["module_validate_contract"]({first})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'engineering["module_validate_graph"]([{first}, {second}])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'engineering["module_validate_graph"]([{second}, {first}])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["module_validate_contract"](["app.main", "../main.rpr", 1, 0, ["run"], [], ["console"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'engineering["module_validate_contract"](["app.main", "main.rpr", 1, 0, ["run"], [], ["pure", "console"]])'
            ),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
