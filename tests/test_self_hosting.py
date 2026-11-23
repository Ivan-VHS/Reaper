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

    def test_reaper_written_typed_ir_builder_runs_in_reference_and_vm(self) -> None:
        root = Path(__file__).resolve().parents[1]
        library = (root / "selfhost/typed_ir.rpr").read_text(encoding="utf-8")
        program = library + '''
make ir := lower_add(19, 23)
when verify_typed_ir(ir) {
    emit "SELFHOST_TYPED_IR_OK"
} otherwise {
    emit "SELFHOST_TYPED_IR_FAIL"
}
emit run_scalar_ir(ir)
'''
        expected = ["SELFHOST_TYPED_IR_OK", "42"]
        for engine in ("treewalk", "vm"):
            output: list[str] = []
            Interpreter(output=output.append).run(program, f"<selfhost-{engine}>", engine=engine)
            self.assertEqual(output, expected)

    def test_reaper_written_verifier_rejects_forward_ssa_references(self) -> None:
        root = Path(__file__).resolve().parents[1]
        library = (root / "selfhost/typed_ir.rpr").read_text(encoding="utf-8")
        program = library + '''
make invalid := [
    {"id": 0, "op": "const", "type": "i64", "value": 1},
    {"id": 1, "op": "add", "type": "i64", "lhs": 1, "rhs": 0}
]
when verify_typed_ir(invalid) {
    emit "SELFHOST_TYPED_IR_BAD"
} otherwise {
    emit "SELFHOST_TYPED_IR_REJECTED"
}
'''
        output: list[str] = []
        Interpreter(output=output.append).run(program, "<selfhost-negative>")
        self.assertEqual(output, ["SELFHOST_TYPED_IR_REJECTED"])


if __name__ == "__main__":
    unittest.main()
