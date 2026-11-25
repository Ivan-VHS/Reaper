from __future__ import annotations

from pathlib import Path
import unittest

from reaper.runtime import Interpreter


ROOT = Path(__file__).resolve().parents[1]


class FrameworkModulesTests(unittest.TestCase):
    def test_all_framework_modules_execute_as_reaper_source(self) -> None:
        source_path = ROOT / "examples" / "frameworks_smoke.rpr"
        output: list[str] = []
        interpreter = Interpreter(output=output.append)

        interpreter.run(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )

        self.assertEqual(output, ["framework smoke checks passed"])


if __name__ == "__main__":
    unittest.main()
