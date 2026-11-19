from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from reaper.compiler_cli import main


class CompilerCliTests(unittest.TestCase):
    def test_cli_emits_ir_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.rpr"
            source.write_text("emit 2 + 2\n", encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                result = main([str(source), "--optimize"])
            payload = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["format"], "quarry-ir")
            self.assertEqual(payload["optimization"]["folded_expressions"], 1)

    def test_cli_rejects_static_type_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.rpr"
            source.write_text('emit "count=" ++ 2\n', encoding="utf-8")
            errors = StringIO()
            with redirect_stderr(errors):
                result = main([str(source)])
            self.assertEqual(result, 1)
            self.assertIn("text-operands", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
