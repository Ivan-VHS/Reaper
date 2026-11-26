from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksFiftyOneToFiftyFiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_51_55.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as governance\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_fifty_five_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('governance["foundation_validate_catalog_55"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(governance["foundation_all_frameworks_55"]())'),
            ["55"],
        )
        self.assertEqual(
            self.run_expression('governance["foundation_all_frameworks_55"]()[54][1]'),
            ["Matrix"],
        )

    def test_standard_rules_have_levels_and_unique_ids(self) -> None:
        self.assertEqual(
            self.run_expression('governance["standard_validate_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('governance["standard_normative_rules"]()'),
            ["[std.bounds, std.effects, std.compatibility]"],
        )
        self.assertEqual(
            self.run_expression('governance["standard_validate_selection"](["std.bounds", "std.audit"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('governance["standard_validate_selection"](["std.bounds", "unknown"])'),
            ["false"],
        )

    def test_regulation_exception_requires_known_policy_and_expiry(self) -> None:
        self.assertEqual(
            self.run_expression('governance["regulation_validate_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('governance["regulation_validate_exception"](["policy.native-ffi-opt-in", "reviewed path", "security-owner", 1900000000, "proposed"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('governance["regulation_validate_exception"](["unknown-policy", "reason", "owner", 1900000000, "proposed"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('governance["regulation_validate_exception"](["policy.native-ffi-opt-in", "reason", "owner", 0, "approved"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('governance["regulation_validate_exceptions"]([["policy.native-ffi-opt-in", "reason", "owner", 1900000000, "approved"]])'),
            ["true"],
        )

    def test_specification_requires_acceptance_for_every_requirement(self) -> None:
        self.assertEqual(
            self.run_expression('governance["specification_validate_descriptor"](["spec.runtime.v1", 1, "bounded runtime", [["R-1", "Requests are bounded", "must"]], [["R-1", "tests/test_runtime_platform.py"]]])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('governance["specification_validate_descriptor"](["spec.runtime.v1", 1, "bounded runtime", [["R-1", "Requests are bounded", "must"], ["R-2", "Failures are explicit", "should"]], [["R-1", "test.py"]]])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('governance["specification_validate_descriptor"](["spec.runtime.v1", 1, "bounded runtime", [["R-1", "Requests are bounded", "required"]], [["R-1", "test.py"]]])'),
            ["false"],
        )

    def test_schema_validates_fields_payloads_and_compatibility(self) -> None:
        schema = '["sample.v1", 1, 0, [["name", "text", true], ["trace", "text", false]], true]'
        self.assertEqual(
            self.run_expression(f'governance["schema_validate_descriptor"]({schema})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'governance["schema_validate_payload"]({schema}, ["Reaper"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'governance["schema_validate_payload"]({schema}, [])'),
            ["false"],
        )
        consumer = '["sample.v1", 1, 0, [["name", "text", true]], false]'
        self.assertEqual(
            self.run_expression(f'governance["schema_validate_compatibility"]({schema}, {consumer})'),
            ["true"],
        )
        incompatible = '["sample.v1", 1, 0, [["name", "number", true]], false]'
        self.assertEqual(
            self.run_expression(f'governance["schema_validate_compatibility"]({schema}, {incompatible})'),
            ["false"],
        )
        changed_major = '["sample.v1", 2, 0, [["name", "text", true]], false]'
        self.assertEqual(
            self.run_expression(f'governance["schema_validate_compatibility"]({schema}, {changed_major})'),
            ["false"],
        )

    def test_matrix_rejects_missing_duplicate_and_unsupported_cells(self) -> None:
        rows = '["lexer", "parser"]'
        columns = '["syntax", "diagnostics"]'
        complete = '[["lexer", "syntax", "covered", "tests/test_lexer.py"], ["lexer", "diagnostics", "partial", "docs/errors/DIAGNOSTICS.md"], ["parser", "syntax", "covered", "tests/test_parser.py"], ["parser", "diagnostics", "missing", ""]]'
        self.assertEqual(
            self.run_expression(f'governance["matrix_validate_complete"]({rows}, {columns}, {complete})'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(f'governance["matrix_validate_cells"]({rows}, {columns}, {complete[:-1]})'),
            ["false"],
        )
        duplicate = '[["lexer", "syntax", "covered", "a"], ["lexer", "syntax", "covered", "b"], ["parser", "syntax", "covered", "c"], ["parser", "diagnostics", "missing", ""]]'
        self.assertEqual(
            self.run_expression(f'governance["matrix_validate_cells"]({rows}, {columns}, {duplicate})'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'governance["matrix_coverage_summary"](["lexer"], ["syntax"], [["lexer", "syntax", "covered", "tests/test_lexer.py"]])'
            ),
            ["[1, 0, 0, 0, 1]"],
        )


if __name__ == "__main__":
    unittest.main()
