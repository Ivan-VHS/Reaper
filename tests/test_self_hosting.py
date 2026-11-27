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

    def test_reaper_written_program_parser_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/program_parser.rpr", "SELFHOST_PROGRAM_PARSER_OK")

    def test_reaper_written_source_map_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/source_map.rpr", "SELFHOST_SOURCE_MAP_OK")

    def test_reaper_written_span_contract_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/span.rpr", "SELFHOST_SPAN_OK")

    def test_reaper_written_token_stream_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/token_stream.rpr", "SELFHOST_TOKEN_STREAM_OK")

    def test_reaper_written_diagnostics_run_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/diagnostics.rpr", "SELFHOST_DIAGNOSTICS_OK")

    def test_reaper_written_line_index_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/line_index.rpr", "SELFHOST_LINE_INDEX_OK")

    def test_reaper_written_ast_contract_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/ast.rpr", "SELFHOST_AST_OK")

    def test_reaper_written_operator_table_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/operator_table.rpr", "SELFHOST_OPERATOR_TABLE_OK")

    def test_reaper_written_unicode_lexer_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/lexer.rpr", "SELFHOST_LEXER_OK")

    def test_reaper_written_type_system_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/type_system.rpr", "SELFHOST_TYPE_SYSTEM_OK")

    def test_reaper_written_ir_verifier_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/ir.rpr", "SELFHOST_IR_OK")

    def test_reaper_written_optimizer_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/optimizer.rpr", "SELFHOST_OPTIMIZER_OK")

    def test_reaper_written_bytecode_engine_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/bytecode.rpr", "SELFHOST_BYTECODE_OK")

    def test_reaper_written_memory_model_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/memory_model.rpr", "SELFHOST_MEMORY_MODEL_OK")

    def test_reaper_written_ownership_model_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/ownership.rpr", "SELFHOST_OWNERSHIP_OK")

    def test_reaper_written_collections_run_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/collections.rpr", "SELFHOST_COLLECTIONS_OK")

    def test_reaper_written_module_graph_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/module_graph.rpr", "SELFHOST_MODULE_GRAPH_OK")

    def test_reaper_written_scope_model_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/scopes.rpr", "SELFHOST_SCOPE_OK")

    def test_reaper_written_generic_unifier_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/generics.rpr", "SELFHOST_GENERICS_OK")

    def test_reaper_written_dabi64_contract_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/dabi64.rpr", "SELFHOST_DABI64_OK")

    def test_reaper_written_hardware_contract_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/hardware_contract.rpr", "SELFHOST_HARDWARE_CONTRACT_OK")

    def test_reaper_processor_kernel_v1_runs_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("examples/processor_kernel.rpr", "REAPER_PROCESSOR_KERNEL_V1_OK")

    def test_reaper_written_lsp_positions_run_on_the_reference_runtime(self) -> None:
        self._run_selfhost_program("selfhost/lsp_positions.rpr", "SELFHOST_LSP_POSITIONS_OK")

if __name__ == "__main__":
    unittest.main()
