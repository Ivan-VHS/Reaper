from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalSoftwareFrameworkSixtySixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_66.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as framework\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_umbrella_catalog_contains_all_sixty_six_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('framework["foundation_validate_catalog_66"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(framework["foundation_all_frameworks_66"]())'),
            ["66"],
        )
        self.assertEqual(
            self.run_expression('framework["foundation_all_frameworks_66"]()[65][1]'),
            ["Software Framework"],
        )

    def test_manifest_has_the_exact_constituent_order(self) -> None:
        self.assertEqual(
            self.run_expression('framework["software_framework_validate_manifest"](framework["software_framework_manifest"]())'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_validate_load_order"](framework["software_framework_ids_65"]())'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_validate_manifest"](["reaper.software-framework.v1", 1, 1, "foundation.software-framework.v1", framework["software_framework_ids_65"](), framework["software_framework_capabilities"](), "partial"])'
            ),
            ["false"],
        )

    def test_profile_selection_rejects_planned_target(self) -> None:
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_validate_profile"](["canonical-vm", "canonical-vm", "hosted-reference", "implemented"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_select_profile"]("freestanding")'
            ),
            ["nothing"],
        )
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_select_profile"]("native-c17-host")[0]'
            ),
            ["native-c17-host"],
        )

    def test_extension_points_and_unique_extension_ids(self) -> None:
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_validate_extension"](["my-host", "host-adapter", "host"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_validate_extension"](["bad", "host-adapter", "unknown-capability"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'framework["software_framework_validate_extensions"]([["my-host", "host-adapter", "host"], ["my-host", "compiler-pass", "compiler"]])'
            ),
            ["false"],
        )

    def test_compatibility_and_integrated_surfaces_are_explicit(self) -> None:
        self.assertEqual(
            self.run_expression('framework["software_framework_validate_compatibility"](1, 0)'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('framework["software_framework_validate_compatibility"](2, 0)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('framework["software_framework_validate_compatibility"](1, 1)'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('framework["software_framework_validate_integration_layers"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(framework["software_framework_safety_contract"]())'),
            ["6"],
        )


if __name__ == "__main__":
    unittest.main()
