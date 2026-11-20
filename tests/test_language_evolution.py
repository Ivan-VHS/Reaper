from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from reaper.language_evolution import (
    MEMORY_SCHEMA,
    OmniCoreEngine,
    _persist_memory,
    main,
)


class OmniCoreIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "grammar").mkdir()
        (self.root / "target").mkdir()
        (self.root / "src" / "worker.py").write_text(
            """from typing import Result

async def fetch(value: int) -> Result:
    with open(value) as handle:
        if value:
            return await handle.read()
    return None

async def transform(items):
    return items.map(lambda item: item)
""",
            encoding="utf-8",
        )
        (self.root / "src" / "worker.rs").write_text(
            """pub enum Outcome { Good, Bad }

pub async fn fetch(value: &mut i32) -> Result<i32, Error> {
    unsafe { value }
}

fn transform(items: Vec<i32>) -> Option<i32> {
    items.iter().map(|x| x).collect()
}
""",
            encoding="utf-8",
        )
        (self.root / "tests" / "worker_test.py").write_text(
            "def test_worker():\n    assert True\n", encoding="utf-8"
        )
        (self.root / "grammar" / "Reaper.g4").write_text(
            "grammar Reaper;\nprogram: expression EOF;\nexpression: IDENTIFIER;\n",
            encoding="utf-8",
        )
        (self.root / "Cargo.toml").write_text(
            '[package]\nname = "foreign-fixture"\nversion = "0.1.0"\nrust-version = "1.78"\n',
            encoding="utf-8",
        )
        (self.root / "runtime.trace.jsonl").write_text(
            '{"event":"call","argument_type":"i32"}\n'
            '{"event":"return","return_type":"Result<i32, Error>"}\n',
            encoding="utf-8",
        )
        (self.root / "target" / "ignored.rs").write_text("fn ignored() {}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_ingests_languages_grammars_manifests_and_runtime_traces(self) -> None:
        report = OmniCoreEngine(self.root).run()
        self.assertEqual(report.languages["python"], 2)
        self.assertEqual(report.languages["rust"], 1)
        self.assertEqual(report.files_analyzed, 3)
        self.assertEqual({item.kind for item in report.artifacts}, {"grammar", "build-manifest", "runtime-trace"})
        trace = next(item for item in report.artifacts if item.kind == "runtime-trace")
        self.assertEqual(trace.metadata["valid_records"], 2)
        self.assertIn("async_await", {item.feature for item in report.evidence})
        self.assertIn("ownership_borrowing", {item.feature for item in report.evidence})
        self.assertTrue(report.proposals)
        self.assertTrue(all(item.proposal_id.startswith("lang-evo-") for item in report.proposals))
        self.assertFalse(report.to_dict()["execution_policy"]["foreign_code_executed"])
        self.assertIn("runtime_type_observations", {item.feature for item in report.evidence})

    def test_python_ast_and_foreign_structural_parser_are_explicit(self) -> None:
        report = OmniCoreEngine(self.root).run()
        by_path = {item.path: item for item in report.files}
        self.assertEqual(by_path["src/worker.py"].parser, "python-ast")
        self.assertEqual(by_path["src/worker.rs"].parser, "structural-lexer")
        self.assertIn("FunctionDecl", by_path["src/worker.rs"].node_counts)
        self.assertIn("TypeDecl", by_path["src/worker.rs"].node_counts)
        self.assertIn("FunctionDecl", by_path["src/worker.py"].node_counts)
        self.assertTrue(by_path["src/worker.py"].uast)
        exported = OmniCoreEngine(self.root).run().to_dict(include_uast=True)
        self.assertIn("uast", exported["files"][0])
        self.assertTrue(exported["knowledge_graph"]["nodes"])

    def test_malformed_python_is_recovered_as_opaque(self) -> None:
        path = self.root / "broken.py"
        path.write_text("def unfinished(:\n    pass\n", encoding="utf-8")
        report = OmniCoreEngine(path).run()
        self.assertEqual(report.files_analyzed, 1)
        self.assertEqual(report.files[0].parser, "python-ast-with-opaque-recovery")
        self.assertTrue(report.files[0].opaque_regions)
        self.assertIn("OpaqueNode", report.files[0].node_counts)

    def test_budgets_are_enforced_and_ignored_directories_are_pruned(self) -> None:
        report = OmniCoreEngine(self.root, max_files=1).run()
        self.assertLessEqual(report.files_analyzed + len(report.artifacts), 1)
        self.assertGreater(report.skipped.get("file-count-limit", 0), 0)
        self.assertNotIn("target/ignored.rs", {item.path for item in report.files})
        with self.assertRaises(ValueError):
            OmniCoreEngine(self.root, max_total_bytes=0)

    def test_proposal_ids_are_deterministic(self) -> None:
        first = OmniCoreEngine(self.root).run()
        second = OmniCoreEngine(self.root).run()
        self.assertEqual(
            [item.proposal_id for item in first.proposals],
            [item.proposal_id for item in second.proposals],
        )

    def test_scan_does_not_modify_source_files(self) -> None:
        path = self.root / "src" / "worker.py"
        before = path.read_bytes()
        OmniCoreEngine(self.root, mode="autonomous").run()
        self.assertEqual(path.read_bytes(), before)

    def test_memory_journal_merges_source_and_feature_provenance(self) -> None:
        report = OmniCoreEngine(self.root).run()
        memory_path = self.root / ".reaper" / "evolution-memory.json"
        _persist_memory(memory_path, report)
        data = json.loads(memory_path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], MEMORY_SCHEMA)
        self.assertIn("src/worker.py", data["sources"])
        self.assertTrue(data["features"])

    def test_cli_refuses_to_overwrite_any_scanned_file(self) -> None:
        protected = self.root / "notes.txt"
        protected.write_text("do not overwrite", encoding="utf-8")
        result = main([str(self.root), "--output", str(protected)])
        self.assertEqual(result, 2)
        self.assertEqual(protected.read_text(encoding="utf-8"), "do not overwrite")

    def test_cli_can_emit_json_and_atomically_write_report(self) -> None:
        output = self.root / "reports" / "absorption.json"
        with contextlib.redirect_stdout(io.StringIO()):
            result = main([str(self.root), "--json", "--output", str(output)])
        self.assertEqual(result, 0)
        data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "reaper-omnicore-report/v1")
        self.assertEqual(data["engine"], "OmniCore Language Evolution Engine")
        self.assertIn("knowledge_graph", data)


if __name__ == "__main__":
    unittest.main()
