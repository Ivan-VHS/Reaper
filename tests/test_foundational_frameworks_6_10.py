from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksSixToTenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_6_10.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as core\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_combined_catalog_contains_ten_unique_foundations(self) -> None:
        self.assertEqual(
            self.run_expression('core["foundation_validate_all_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(core["foundation_all_frameworks"]())'),
            ["10"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_all_frameworks"]()[9][1]'),
            ["Backbone"],
        )

    def test_basis_checks_value_kinds_effects_and_ownership(self) -> None:
        self.assertEqual(
            self.run_expression('core["basis_validate_value_kind"]("resource")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["basis_validate_value_kind"]("pointer")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["basis_validate_effects"](["filesystem", "clock"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["basis_validate_effects"](["pure", "network"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["basis_validate_effects"](["unknown-effect"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["basis_validate_ownership"]("borrow_mut")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["basis_validate_ownership"]("implicit-global")'),
            ["false"],
        )

    def test_versioned_contract_validation(self) -> None:
        self.assertEqual(
            self.run_expression(
                'core["core_foundation_validate_contract"](["reaper.host-service.v1", 1, 0, "both"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'core["core_foundation_validate_contract"](["reaper.host-service.v1", 2, 0, "both"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'core["core_foundation_validate_contract"](["reaper.host-service.v1", 1, 1, "both"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'core["core_foundation_validate_contract"](["unknown.contract", 1, 0, "both"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'core["core_foundation_validate_contract"](["reaper.host-service.v1", 1.5, 0, "both"])'
            ),
            ["false"],
        )

    def test_root_context_and_import_boundaries(self) -> None:
        self.assertEqual(
            self.run_expression(
                'core["root_validate_context"](["reaper", "src", "frameworks", "build", "hosted-reference"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'core["root_validate_context"](["reaper", "/src", "frameworks", "build", "hosted-reference"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["root_validate_relative_path"]("../outside")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["root_validate_import_edge"](["module-a", "module-b"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["root_validate_import_edge"](["module-a", "module-a"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["root_validate_import_specifier"]("modules/math.rpr")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["root_validate_import_specifier"]("../escape.rpr")'),
            ["false"],
        )

    def test_skeleton_requires_core_components_and_rejects_unknowns(self) -> None:
        self.assertEqual(
            self.run_expression(
                'core["skeleton_validate_components"](["manifest", "entry", "modules", "tests"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'core["skeleton_validate_components"](["manifest", "entry", "tests"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'core["skeleton_validate_components"](["manifest", "entry", "modules", "tests", "unknown"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'core["skeleton_validate_components"](["manifest", "entry", "modules", "tests", "tests"])'
            ),
            ["false"],
        )

    def test_backbone_contracts_match_first_group_architecture(self) -> None:
        self.assertEqual(
            self.run_expression(
                'core["backbone_validate_edges"](core["backbone_edges"]())'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'core["backbone_find_edge"]("parser", "semantic-analysis")[2]'
            ),
            ["syntax-tree.v1"],
        )
        self.assertEqual(
            self.run_expression(
                'core["backbone_validate_edges"]([["source", "parser", "wrong.v1", "implemented"]])'
            ),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
