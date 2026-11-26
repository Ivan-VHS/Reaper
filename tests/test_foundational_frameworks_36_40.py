from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter


class FoundationalFrameworksThirtySixToFortyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = (
            Path(__file__).resolve().parents[1]
            / "frameworks"
            / "foundation_36_40.rpr"
        ).resolve()

    def run_expression(self, expression: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "check.rpr"
            source = (
                f'import "{self.module.as_posix()}" as concepts\n'
                f"emit {expression}\n"
            )
            entry.write_text(source, encoding="utf-8")
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            return output

    def test_catalog_extends_to_forty_unique_frameworks(self) -> None:
        self.assertEqual(
            self.run_expression('concepts["foundation_validate_catalog_40"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('size(concepts["foundation_all_frameworks_40"]())'),
            ["40"],
        )
        self.assertEqual(
            self.run_expression('concepts["foundation_all_frameworks_40"]()[39][1]'),
            ["Concept"],
        )

    def test_context_and_source_spans_are_bounded(self) -> None:
        self.assertEqual(
            self.run_expression(
                'concepts["context_validate_descriptor"](["src/main.rpr", "app.main", "uk", "analysis", "hosted-reference"])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'concepts["context_validate_descriptor"](["src/main.rpr", "app.main", "xx", "analysis", "hosted-reference"])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('concepts["context_validate_span"]([10, 18, 2, 4])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('concepts["context_validate_span"]([18, 10, 2, 4])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('concepts["context_validate_span"]([10, 18, 0, 4])'),
            ["false"],
        )

    def test_model_record_checks_types_and_unique_fields(self) -> None:
        self.assertEqual(
            self.run_expression(
                'concepts["model_validate_record"](["gpio.pin.v1", [["pin", "u8", false], ["enabled", "boolean", true]]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'concepts["model_validate_record"](["gpio.pin.v1", [["pin", "u8", false], ["pin", "boolean", true]]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'concepts["model_validate_record"](["gpio.pin.v1", [["address", "pointer", false]]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('concepts["model_validate_runtime_kind"]("resource")'),
            ["true"],
        )

    def test_pattern_requires_its_declared_constructs(self) -> None:
        self.assertEqual(
            self.run_expression(
                'concepts["pattern_validate_request"](["module-boundary", ["import", "export", "cycle-check"]])'
            ),
            ["true"],
        )
        self.assertEqual(
            self.run_expression(
                'concepts["pattern_validate_request"](["module-boundary", ["import", "export"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression(
                'concepts["pattern_validate_request"](["unknown", ["import", "export"]])'
            ),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('concepts["pattern_find_by_domain"]("runtime")'),
            ["[bounded-collections, managed-resource]"],
        )

    def test_paradigm_catalog_rejects_planned_mode(self) -> None:
        self.assertEqual(
            self.run_expression('concepts["paradigm_validate_selection"](["flow-first", "classic", "most"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('concepts["paradigm_validate_profile"]("qcs-dsl")'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('concepts["paradigm_validate_profile"]("systems-syntax")'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('concepts["paradigm_validate_selection"](["flow-first", "flow-first"])'),
            ["false"],
        )

    def test_concept_graph_rejects_unknown_nodes_and_relations(self) -> None:
        self.assertEqual(
            self.run_expression('concepts["concept_validate_catalog"]()'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('concepts["concept_validate_link"](["concept.value-model", "concept.canonical-ir", "feeds"])'),
            ["true"],
        )
        self.assertEqual(
            self.run_expression('concepts["concept_validate_link"](["concept.value-model", "unknown", "feeds"])'),
            ["false"],
        )
        self.assertEqual(
            self.run_expression('concepts["concept_validate_link"](["concept.value-model", "concept.canonical-ir", "unknown-relation"])'),
            ["false"],
        )


if __name__ == "__main__":
    unittest.main()
