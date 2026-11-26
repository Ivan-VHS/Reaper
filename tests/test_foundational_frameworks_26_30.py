from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksTwentySixToThirtyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_26_30.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as base\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_thirty_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('base["foundation_validate_catalog_30"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(base["foundation_all_frameworks_30"]())'),
            ["30"],
        )
        self.assertEqual(
            self.run_expression('base["foundation_all_frameworks_30"]()[29][1]'),
            ["Base Layer"],
        )

    def test_technology_stack_selection_obeys_maturity(self) -> None:
        self.assertEqual(
            self.run_expression('base["technology_stack_validate_selection"]("hosted-c17-x86_64")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('base["technology_stack_validate_selection"]("armv7m-firmware")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('base["technology_stack_validate_selection"]("unknown-target")'),
            ["false"],
        )

    def test_template_requires_exact_nonempty_unique_bindings(self) -> None:
        self.assertEqual(
            self.run_expression(
                'base["template_validate_request"](["cli-tool", [["project_name", "sample"], ["entry_module", "main.rpr"]]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'base["template_validate_request"](["cli-tool", [["project_name", "sample"]]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'base["template_validate_request"](["cli-tool", [["project_name", "sample"], ["project_name", "other"]]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'base["template_validate_request"](["cli-tool", [["project_name", ""], ["entry_module", "main.rpr"]]])'
            ),
            ["false"],
        )

    def test_skeleton_alias_points_to_existing_canonical_framework(self) -> None:
        self.assertEqual(
            self.run_expression('base["skeleton_alias_resolve"]("Skeleton")'),
            ["foundation.skeleton.v1"],
        )
        self.assertEqual(
            self.run_expression(
                'base["skeleton_alias_validate"](["foundation.skeleton.alias.v1", "Skeleton", "foundation.skeleton.v1", "canonical-alias"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('base["skeleton_alias_resolve"]("Unknown")'),
            ["nothing"],
        )

    def test_boilerplate_is_reusable_source_not_an_execution_action(self) -> None:
        self.assertEqual(
            self.run_expression('base["boilerplate_source"]("identity-function")'),
            ["craft identity(value) { yield value }"],
        )
        self.assertEqual(
            self.run_expression('base["boilerplate_validate_selection"](["minimal-entry", "exported-constant"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('base["boilerplate_validate_selection"](["unknown"])'),
            ["false"],
        )

    def test_base_layer_requires_implemented_language_core(self) -> None:
        required = '["core-syntax", "scopes-and-bindings", "module-loading", "reference-runtime", "resource-limits"]'
        self.assertEqual(
            self.run_expression(f'base["base_layer_validate_profile"]({required})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'base["base_layer_validate_profile"](["core-syntax", "reference-runtime"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('base["base_layer_status"]("canonical-ir")'),
            ["partial"],
        )
        self.assertEqual(
            self.run_expression('base["base_layer_status"]("unknown-feature")'),
            ["nothing"],
        )


if __name__ == "__main__":
    unittest.main()
