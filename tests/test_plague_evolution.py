from __future__ import annotations

import unittest
from pathlib import Path

from reaper import Interpreter


class PlagueEvolutionTests(unittest.TestCase):
    def test_reaper_native_policy_smoke(self) -> None:
        program = Path(__file__).resolve().parents[1] / "plague" / "examples" / "evolution_smoke.rpr"
        output: list[str] = []
        Interpreter(output=output.append).run(
            program.read_text(encoding="utf-8"),
            str(program),
        )
        self.assertEqual(output, ["PLAGUE_V1_OK"])


if __name__ == "__main__":
    unittest.main()
