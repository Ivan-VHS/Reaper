from __future__ import annotations

from pathlib import Path
import unittest

from reaper.runtime import Interpreter


ROOT = Path(__file__).resolve().parents[1]


class FrameworkFederationHandlerTests(unittest.TestCase):
    def test_all_120_federation_operations_run_as_reaper_source(self) -> None:
        source_path = ROOT / "examples" / "frameworks" / "federation_handlers_smoke.rpr"
        output: list[str] = []
        interpreter = Interpreter(output=output.append)

        interpreter.run(
            source_path.read_text(encoding="utf-8"),
            filename=str(source_path),
        )

        self.assertEqual(
            output,
            ["all 120 Reaper framework federation handler checks passed"],
        )


if __name__ == "__main__":
    unittest.main()
