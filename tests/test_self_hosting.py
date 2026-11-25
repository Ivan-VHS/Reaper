from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter


class SelfHostingBootstrapTests(unittest.TestCase):
    def _run_selfhost_program(self, relative_path: str, expected: str) -> None:
        program = Path(__file__).resolve().parents[1] / relative_path
        output: list[str] = []
        Interpreter(output=output.append).run(program.read_text(encoding="utf-8"), str(program))
        self.assertEqual(output, [expected])

    def test_reaper_written_lexer_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/lexer.rpr", "SELFHOST_LEXER_OK")

    def test_reaper_written_parser_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/parser.rpr", "SELFHOST_PARSER_OK")

    def test_reaper_written_source_map_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/source_map.rpr", "SELFHOST_SOURCE_MAP_OK")

    def test_reaper_written_diagnostics_run_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/diagnostics.rpr", "SELFHOST_DIAGNOSTICS_OK")

    def test_reaper_written_ir_lowerer_and_verifier_run_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/ir.rpr", "SELFHOST_IR_OK")

    def test_reaper_written_bytecode_lowerer_and_verifier_run_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/bytecode.rpr", "SELFHOST_BYTECODE_OK")

    def test_reaper_written_module_graph_resolver_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/module_graph.rpr", "SELFHOST_MODULE_GRAPH_OK")

    def test_reaper_written_optimizer_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/optimizer.rpr", "SELFHOST_OPTIMIZER_OK")


if __name__ == "__main__":
    unittest.main()
