from __future__ import annotations

import json
import unittest
from pathlib import Path

from reaper import Interpreter
from reaper.lexer import tokenize
from reaper.parser import parse


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


    def test_reaper_written_typed_records_and_platform_abi_run(self) -> None:
        program = Path(__file__).resolve().parents[1] / "selfhost/type_declarations.rpr"
        output: list[str] = []
        Interpreter(output=output.append).run(program.read_text(encoding="utf-8"), str(program))
        self.assertEqual(output[-1], "SELFHOST_TYPE_DECLARATIONS_OK")
        self.assertIn("SELFHOST_LEXER_OK", output)
        self.assertIn("SELFHOST_PROGRAM_PARSER_OK", output)

    def test_program_parser_matches_reference_ast_for_full_statement_sample(self) -> None:
        source = '''import "math.rpr" as math
export make base := 10
craft adjust(value, delta) {
    when value < 0 {
        yield -value
    } otherwise {
        yield value :: add(delta)
    }
}
each item in [1, 2, 3] {
    emit adjust(item, 1)
}
loop while false {
    emit "never"
}
'''
        tokens = [
            [token.kind, token.value, token.line, token.column]
            for token in tokenize(source, "parity.rpr")
        ]

        def normalize(node):
            value = list(node.value) if isinstance(node.value, tuple) else node.value
            children = [normalize(child) for child in (node.children or [])]
            token = [node.token.kind, node.token.value, node.token.line, node.token.column]
            return [node.kind, token, value, children]

        def reaper_literal(value):
            if value is None:
                return "nothing"
            if value is True:
                return "true"
            if value is False:
                return "false"
            if isinstance(value, str):
                return json.dumps(value, ensure_ascii=False)
            if isinstance(value, (int, float)):
                return repr(value)
            if isinstance(value, (list, tuple)):
                return "[" + ", ".join(reaper_literal(item) for item in value) + "]"
            raise TypeError(f"unsupported AST value: {type(value).__name__}")

        expected = reaper_literal(normalize(parse(source, "parity.rpr")))
        token_literal = reaper_literal(tokens)
        parser_path = Path(__file__).resolve().parents[1] / "selfhost/program_parser.rpr"
        program = parser_path.read_text(encoding="utf-8")
        program += (
            "\nmake parity_result := parse_program(" + token_literal + ")\n"
            'assert(parity_result[0] == "OK", "statement parser rejected the parity sample")\n'
            "assert(parity_result[1] == " + expected + ', "Reaper AST differs from reference AST")\n'
        )

        output: list[str] = []
        Interpreter(output=output.append).run(program, str(parser_path))
        self.assertEqual(output, ["SELFHOST_PROGRAM_PARSER_OK"])


if __name__ == "__main__":
    unittest.main()
