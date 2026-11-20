from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter


class SelfHostingBootstrapTests(unittest.TestCase):
    def test_reaper_written_lexer_runs_on_the_reference_runtime(self) -> None:
        program = Path(__file__).resolve().parents[1] / "selfhost" / "lexer.rpr"
        output: list[str] = []
        Interpreter(output=output.append).run(program.read_text(encoding="utf-8"), str(program))
        self.assertEqual(output, ["SELFHOST_LEXER_OK"])


if __name__ == "__main__":
    unittest.main()
