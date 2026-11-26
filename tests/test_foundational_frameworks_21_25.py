from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksTwentyOneToTwentyFiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_21_25.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as tools\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_twenty_five_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('tools["foundation_validate_catalog_25"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(tools["foundation_all_frameworks_25"]())'),
            ["25"],
        )
        self.assertEqual(
            self.run_expression('tools["foundation_all_frameworks_25"]()[24][1]'),
            ["Stack"],
        )

    def test_toolset_inventory_and_selection(self) -> None:
        self.assertEqual(
            self.run_expression('tools["toolset_validate_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["toolset_validate_selection"](["reaper.cli", "reaper.formatter"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["toolset_validate_selection"](["reaper.cli", "unknown.tool"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["toolset_validate_selection"](["reaper.cli", "reaper.cli"])'),
            ["false"],
        )

    def test_tool_discovery_report_is_validated_without_execution(self) -> None:
        self.assertEqual(
            self.run_expression('tools["tooling_validate_probe"](["gcc", "/usr/bin/gcc", "available"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["tooling_validate_probe"](["gcc", "", "missing"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["tooling_validate_probe"](["gcc", "/usr/bin/gcc", "not-probed"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["tooling_validate_probe"](["unknown-compiler", "/usr/bin/unknown", "available"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["tooling_validate_probe"](["gcc", "", "installed"])'),
            ["false"],
        )

    def test_toolkit_bundles_resolve_deterministically(self) -> None:
        self.assertEqual(
            self.run_expression('tools["toolkit_validate_selection"](["language", "native-build"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["toolkit_validate_selection"](["language", "missing"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["toolkit_validate_selection"](["language", "language"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["toolkit_resolve_tools"](["language", "native-build"])'),
            ["[reaper.cli, reaper.formatter, reaper.typecheck, reaper.native_compiler, reaper.systems_architectures]"],
        )

    def test_package_graph_requires_unique_dependency_first_order(self) -> None:
        valid = '[["math", 1, 0, "math.rpr", []], ["app", 1, 0, "main.rpr", ["math"]]]'
        self.assertEqual(
            self.run_expression(f'tools["package_validate_registry"]({valid})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'tools["package_resolve_order"]({valid})'),
            ["[math, app]"],
        )
        forward = '[["app", 1, 0, "main.rpr", ["math"]], ["math", 1, 0, "math.rpr", []]]'
        self.assertEqual(
            self.run_expression(f'tools["package_validate_registry"]({forward})'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["package_validate_manifest"](["math", 1.5, 0, "math.rpr", []])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["package_validate_manifest"](["math", 1, 0, "main.txt", []])'),
            ["false"],
        )

    def test_stack_profiles_preserve_layer_order_and_maturity(self) -> None:
        self.assertEqual(
            self.run_expression('tools["stack_validate_selection"]("canonical-vm")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["stack_validate_selection"]("freestanding")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["stack_validate_selection"]("unknown-stack")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('tools["stack_validate_layers"](["source", "lexer", "parser", "semantic-analysis"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('tools["stack_validate_layers"](["source", "lexer", "lexer", "parser"])'),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
