from __future__ import annotations

import unittest
from pathlib import Path

from reaper.runtime import Interpreter


class ReaperCompilerFoundationPrograms(unittest.TestCase):
    def run_program(self, relative_path: str, expected: str) -> list[str]:
        path = Path(__file__).resolve().parents[1] / relative_path
        output: list[str] = []
        Interpreter(output=output.append).run(
            path.read_text(encoding="utf-8"), str(path)
        )
        self.assertEqual(output[-1], expected)
        return output

    def test_generic_result_option_and_effect_contracts(self) -> None:
        self.run_program("selfhost/type_system.rpr", "SELFHOST_TYPE_SYSTEM_OK")

    def test_region_borrow_and_deterministic_drop_contracts(self) -> None:
        self.run_program("selfhost/ownership.rpr", "SELFHOST_OWNERSHIP_OK")

    def test_typed_hir_mir_lir_span_preservation(self) -> None:
        self.run_program("selfhost/typed_pipeline.rpr", "SELFHOST_TYPED_PIPELINE_OK")

    def test_offline_package_manifest_and_lock_contract(self) -> None:
        self.run_program("selfhost/package_contract.rpr", "SELFHOST_PACKAGE_CONTRACT_OK")


if __name__ == "__main__":
    unittest.main()
