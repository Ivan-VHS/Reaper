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

    def test_combined_catalog_aligns_with_native_concept_names(self) -> None:
        self.assertEqual(
            self.run_expression('core["foundation_validate_all_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(core["foundation_all_frameworks"]())'),
            ["10"],
        )
        expected = [
            ("architecture.basis.v1", "Basis"),
            ("architecture.base.v1", "Base"),
            ("architecture.foundation.v1", "Foundation"),
            ("architecture.skeleton.v1", "Skeleton"),
            ("architecture.backbone.v1", "Backbone"),
        ]
        for index, (identifier, name) in enumerate(expected, start=5):
            self.assertEqual(
                self.run_expression(
                    f'core["foundation_all_frameworks"]()[{index}][0]'
                ),
                [identifier],
            )
            self.assertEqual(
                self.run_expression(
                    f'core["foundation_all_frameworks"]()[{index}][1]'
                ),
                [name],
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
            self.run_expression('core["basis_validate_effects"](["clock", "clock"])'),
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

    def test_base_requires_real_shared_primitives(self) -> None:
        self.assertEqual(
            self.run_expression('core["base_validate_selection"](["module-loader", "canonical-ir", "resource-ledger", "memory-manager", "diagnostic-catalog"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["base_validate_selection"](["module-loader", "canonical-ir", "resource-ledger", "memory-manager"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["base_validate_selection"](["module-loader", "canonical-ir", "resource-ledger", "memory-manager", "diagnostic-catalog", "unknown"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["base_validate_selection"](["module-loader", "canonical-ir", "resource-ledger", "memory-manager", "diagnostic-catalog", "diagnostic-catalog"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["base_find_primitive"]("host-dispatch")[2]'),
            ["partial"],
        )
        self.assertEqual(
            self.run_expression('core["base_validate_primitive"](["module-loader", "reaper.modules", "implemented", "explicit imports, exports, bounded depth and cycle diagnostics"])'),
            ["true"],
        )

    def test_foundation_contracts_enforce_version_and_direction(self) -> None:
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract"](["reaper.host-service.v1", 1, 0, "both"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract"](["reaper.host-service.v1", 2, 0, "both"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract"](["reaper.host-service.v1", 1, 1, "both"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract"](["unknown.contract", 1, 0, "both"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract"](["reaper.host-service.v1", 1.5, 0, "both"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract"](["reaper.host-service.v1", 1, 0, "sideways"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_contract_catalog"]()'),
            ["true"],
        )

    def test_foundation_invariant_inventory_is_complete_and_unique(self) -> None:
        self.assertEqual(
            self.run_expression('core["foundation_validate_invariants"](["basis.immutability.v1", "basis.bounds.v1", "basis.effects.v1", "basis.ownership.v1"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_invariants"](["basis.immutability.v1", "basis.bounds.v1"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_invariants"](["basis.immutability.v1", "basis.bounds.v1", "basis.effects.v1", "basis.ownership.v1", "unknown"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_invariants"](["basis.immutability.v1", "basis.bounds.v1", "basis.effects.v1", "basis.ownership.v1", "basis.ownership.v1"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["foundation_validate_invariants"]("not-a-list")'),
            ["false"],
        )

    def test_skeleton_requires_core_components_and_rejects_unknowns(self) -> None:
        self.assertEqual(
            self.run_expression('core["skeleton_validate_components"](["manifest", "entry", "modules", "tests"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["skeleton_validate_components"](["manifest", "entry", "tests"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["skeleton_validate_components"](["manifest", "entry", "modules", "tests", "unknown"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('core["skeleton_validate_components"](["manifest", "entry", "modules", "tests", "tests"])'),
            ["false"],
        )

    def test_backbone_contracts_match_first_group_architecture(self) -> None:
        self.assertEqual(
            self.run_expression('core["backbone_validate_edges"](core["backbone_edges"]())'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('core["backbone_find_edge"]("parser", "semantic-analysis")[2]'),
            ["syntax-tree.v1"],
        )
        self.assertEqual(
            self.run_expression('core["backbone_validate_edges"]([["source", "parser", "wrong.v1", "implemented"]])'),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
